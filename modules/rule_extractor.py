"""
Rule-based Entity Extraction Module
Uses regex patterns and spaCy Matcher for structured information extraction
"""

import re
from typing import Dict, List, Tuple, Optional
import spacy
from spacy.matcher import Matcher

from config import Config
from utils.logger import setup_logger

class RuleExtractor:
    """Rule-based entity extractor using regex patterns and spaCy Matcher"""
    
    def __init__(self):
        self.config = Config()
        self.logger = setup_logger('rule_extractor')
        self.nlp = self._load_spacy_model()
        self.matcher = Matcher(self.nlp.vocab)
        self._setup_patterns()
    
    def _load_spacy_model(self):
        """Load spaCy model for pattern matching"""
        try:
            nlp = spacy.load(self.config.SPACY_MODEL)
            return nlp
        except OSError:
            try:
                nlp = spacy.load("en_core_web_sm")
                return nlp
            except OSError:
                self.logger.warning("No spaCy model available, using basic English")
                from spacy.lang.en import English
                return English()
    
    def _setup_patterns(self):
        """Setup spaCy Matcher patterns"""
        try:
            # Name patterns
            name_patterns = [
                [{"IS_TITLE": True}, {"IS_TITLE": True}],  # First Last
                [{"TEXT": {"REGEX": r"^(Mr|Ms|Mrs)$"}}, {"IS_TITLE": True}, {"IS_TITLE": True}],  # Title First Last
                [{"TEXT": "I"}, {"TEXT": "am"}, {"IS_TITLE": True}, {"IS_TITLE": True}],  # I am First Last
                [{"TEXT": "name"}, {"TEXT": "is"}, {"IS_TITLE": True}, {"IS_TITLE": True}],  # name is First Last
            ]
            
            # Date patterns
            date_patterns = [
                [{"TEXT": {"REGEX": r"^\d{1,2}$"}}, {"TEXT": {"REGEX": r"^(st|nd|rd|th)$"}}, {"TEXT": {"REGEX": r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"}}],
                [{"TEXT": {"REGEX": r"^\d{1,2}$"}}, {"TEXT": "/"}, {"TEXT": {"REGEX": r"^\d{1,2}$"}}, {"TEXT": "/"}, {"TEXT": {"REGEX": r"^\d{2,4}$"}}],
            ]
            
            # Budget patterns
            budget_patterns = [
                [{"TEXT": {"REGEX": r"^(Rs|INR|₹)$"}}, {"TEXT": {"REGEX": r"^\d+$"}}],
                [{"TEXT": {"REGEX": r"^budget$"}}, {"TEXT": {"REGEX": r"^(is|around|approximately)$"}}, {"TEXT": {"REGEX": r"^(Rs|INR|₹)$"}}, {"TEXT": {"REGEX": r"^\d+$"}}],
            ]
            
            # Add patterns to matcher
            self.matcher.add("NAME_PATTERN", name_patterns)
            self.matcher.add("DATE_PATTERN", date_patterns) 
            self.matcher.add("BUDGET_PATTERN", budget_patterns)
            
            self.logger.info("spaCy patterns setup completed")
            
        except Exception as e:
            self.logger.error(f"Pattern setup error: {str(e)}")
    
    def extract_emails(self, text: str) -> List[str]:
        """
        Extract email addresses from text
        
        Args:
            text: Input text
            
        Returns:
            List of email addresses
        """
        pattern = self.config.REGEX_PATTERNS['email']
        emails = re.findall(pattern, text, re.IGNORECASE)
        return list(set(emails))  # Remove duplicates
    
    def extract_phone_numbers(self, text: str) -> List[str]:
        """
        Extract phone numbers from text
        
        Args:
            text: Input text
            
        Returns:
            List of phone numbers
        """
        pattern = self.config.REGEX_PATTERNS['phone']
        phones = re.findall(pattern, text)
        
        # Clean and format phone numbers
        cleaned_phones = []
        for phone in phones:
            # Remove non-digits except +
            cleaned = re.sub(r'[^\d+]', '', phone)
            if len(cleaned) >= 10:  # Valid phone number length
                cleaned_phones.append(cleaned)
        
        return list(set(cleaned_phones))
    
    def extract_currency_amounts(self, text: str) -> List[Dict[str, str]]:
        """
        Extract currency amounts from text
        
        Args:
            text: Input text
            
        Returns:
            List of currency amounts with currency type
        """
        amounts = []
        
        # Extract INR amounts
        inr_pattern = self.config.REGEX_PATTERNS['currency_inr']
        inr_matches = re.findall(inr_pattern, text, re.IGNORECASE)
        for match in inr_matches:
            amounts.append({
                'amount': match,
                'currency': 'INR',
                'normalized': self._normalize_amount(match)
            })
        
        # Extract USD amounts
        usd_pattern = self.config.REGEX_PATTERNS['currency_usd']
        usd_matches = re.findall(usd_pattern, text, re.IGNORECASE)
        for match in usd_matches:
            amounts.append({
                'amount': match,
                'currency': 'USD',
                'normalized': self._normalize_amount(match)
            })
        
        return amounts
    
    def _normalize_amount(self, amount_str: str) -> float:
        """
        Normalize currency amount to float
        
        Args:
            amount_str: Raw amount string
            
        Returns:
            Normalized amount as float
        """
        try:
            # Remove currency symbols and clean
            cleaned = re.sub(r'[^\d.,]', '', amount_str)
            cleaned = cleaned.replace(',', '')
            
            # Handle different decimal formats
            if '.' in cleaned:
                return float(cleaned)
            else:
                return float(cleaned)
        except:
            return 0.0
    
    def extract_dates(self, text: str) -> List[str]:
        """
        Extract dates using multiple patterns
        
        Args:
            text: Input text
            
        Returns:
            List of extracted dates
        """
        dates = []
        
        for pattern in self.config.REGEX_PATTERNS['date_patterns']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        # Additional date patterns
        additional_patterns = [
            r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',  # DD/MM/YYYY or DD-MM-YYYY
            r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',    # YYYY/MM/DD or YYYY-MM-DD
        ]
        
        for pattern in additional_patterns:
            matches = re.findall(pattern, text)
            dates.extend(matches)
        
        return list(set(dates))
    
    def extract_traveler_count(self, text: str) -> List[str]:
        """
        Extract number of travelers
        
        Args:
            text: Input text
            
        Returns:
            List of traveler counts
        """
        pattern = self.config.REGEX_PATTERNS['traveler_count']
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        # Extract just the numbers
        counts = []
        for match in matches:
            if isinstance(match, tuple):
                counts.append(match[0])
            else:
                counts.append(match)
        
        return counts
    
    def extract_duration(self, text: str) -> List[str]:
        """
        Extract trip duration
        
        Args:
            text: Input text
            
        Returns:
            List of durations
        """
        pattern = self.config.REGEX_PATTERNS['duration']
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        durations = []
        for match in matches:
            if isinstance(match, tuple):
                durations.append(f"{match[0]} {match[1]}")
            else:
                durations.append(match)
        
        return durations
    
    def extract_destinations(self, text: str) -> List[str]:
        """
        Extract destination mentions
        
        Args:
            text: Input text
            
        Returns:
            List of destinations
        """
        destinations = []
        text_lower = text.lower()
        
        # Check against known destinations
        for destination in self.config.INDIAN_DESTINATIONS:
            if destination in text_lower:
                # Find original case in text
                pattern = re.compile(re.escape(destination), re.IGNORECASE)
                matches = pattern.findall(text)
                destinations.extend(matches)
        
        # Additional destination patterns
        destination_patterns = [
            r'\bto\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # "to Destination"
            r'\bvisit\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # "visit Destination"
            r'\btrip\s+to\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # "trip to Destination"
        ]
        
        for pattern in destination_patterns:
            matches = re.findall(pattern, text)
            destinations.extend(matches)
        
        return list(set(destinations))
    
    def extract_names_with_patterns(self, text: str) -> List[str]:
        """
        Extract names using various patterns
        
        Args:
            text: Input text
            
        Returns:
            List of extracted names
        """
        names = []
        
        # Pattern 1: "I am [Name]" or "My name is [Name]"
        name_patterns = [
            r'\bI\s+am\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
            r'\bmy\s+name\s+is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
            r'\bI\'m\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
            r'\bname:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            names.extend(matches)
        
        # Use spaCy matcher
        try:
            doc = self.nlp(text)
            matches = self.matcher(doc)
            
            for match_id, start, end in matches:
                label = self.nlp.vocab.strings[match_id]
                if label == "NAME_PATTERN":
                    span = doc[start:end]
                    names.append(span.text)
        except Exception as e:
            self.logger.error(f"spaCy matcher error: {str(e)}")
        
        return list(set(names))
    
    def extract_contact_info(self, text: str) -> Dict[str, List[str]]:
        """
        Extract all contact information
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with emails and phone numbers
        """
        return {
            'emails': self.extract_emails(text),
            'phones': self.extract_phone_numbers(text)
        }
    
    def extract_all_entities(self, text: str) -> Dict[str, any]:
        """
        Extract all entities using rule-based methods
        
        Args:
            text: Input text for extraction
            
        Returns:
            Dictionary with all extracted entities
        """
        try:
            entities = {
                'names': self.extract_names_with_patterns(text),
                'destinations': self.extract_destinations(text),
                'dates': self.extract_dates(text),
                'currency_amounts': self.extract_currency_amounts(text),
                'traveler_counts': self.extract_traveler_count(text),
                'durations': self.extract_duration(text),
                'contact_info': self.extract_contact_info(text),
                'method': 'RULE_BASED'
            }
            
            self.logger.debug(f"Rule-based extraction completed")
            return entities
            
        except Exception as e:
            self.logger.error(f"Rule-based extraction error: {str(e)}")
            return {
                'names': [],
                'destinations': [],
                'dates': [],
                'currency_amounts': [],
                'traveler_counts': [],
                'durations': [],
                'contact_info': {'emails': [], 'phones': []},
                'method': 'RULE_BASED_ERROR'
            }
    
    def get_extraction_patterns(self) -> Dict[str, List[str]]:
        """
        Get all regex patterns used for extraction
        
        Returns:
            Dictionary of patterns by category
        """
        return {
            'email': [self.config.REGEX_PATTERNS['email']],
            'phone': [self.config.REGEX_PATTERNS['phone']],
            'currency_inr': [self.config.REGEX_PATTERNS['currency_inr']],
            'currency_usd': [self.config.REGEX_PATTERNS['currency_usd']],
            'dates': self.config.REGEX_PATTERNS['date_patterns'],
            'traveler_count': [self.config.REGEX_PATTERNS['traveler_count']],
            'duration': [self.config.REGEX_PATTERNS['duration']]
        }

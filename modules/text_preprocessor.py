"""
Text Preprocessing Module
Handles text cleaning, normalization, and preprocessing for multilingual content
"""

import re
import string
import unicodedata
from typing import Dict, List, Optional
import spacy
from spacy.lang.en import English

from config import Config
from utils.logger import setup_logger

class TextPreprocessor:
    """Handles text preprocessing for multilingual customer inquiries"""
    
    def __init__(self):
        self.config = Config()
        self.logger = setup_logger('text_preprocessor')
        self.nlp = self._load_spacy_model()
        
        # Devanagari script range for Hindi text detection
        self.hindi_pattern = re.compile(r'[\u0900-\u097F]+')
        
        # Common noise patterns
        self.noise_patterns = [
            r'[^\w\s@.-]',  # Remove special characters except email/phone related
            r'\s+',  # Multiple spaces
            r'^\s+|\s+$'  # Leading/trailing spaces
        ]
    
    def _load_spacy_model(self):
        """Load spaCy model with fallback"""
        try:
            nlp = spacy.load(self.config.SPACY_MODEL)
            self.logger.info(f"Loaded spaCy model: {self.config.SPACY_MODEL}")
            return nlp
        except OSError:
            self.logger.warning(f"Could not load {self.config.SPACY_MODEL}, using basic English model")
            try:
                nlp = spacy.load("en_core_web_sm")
                return nlp
            except OSError:
                self.logger.warning("No spaCy model available, creating basic tokenizer")
                return English()
    
    def detect_languages(self, text: str) -> Dict[str, bool]:
        """
        Detect languages present in the text
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dict with language detection results
        """
        languages = {
            'english': False,
            'hindi': False,
            'hinglish': False
        }
        
        # Check for Hindi (Devanagari script)
        if self.hindi_pattern.search(text):
            languages['hindi'] = True
        
        # Check for English (basic heuristic)
        english_words = re.findall(r'\b[a-zA-Z]+\b', text)
        if len(english_words) > 0:
            languages['english'] = True
        
        # Hinglish detection (mixed script)
        if languages['hindi'] and languages['english']:
            languages['hinglish'] = True
        
        return languages
    
    def normalize_unicode(self, text: str) -> str:
        """
        Normalize Unicode characters
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        # Normalize Unicode to handle various encodings
        normalized = unicodedata.normalize('NFKD', text)
        
        # Convert to ASCII if possible, otherwise keep Unicode
        try:
            # Try to encode/decode to handle mixed encodings
            normalized = normalized.encode('utf-8').decode('utf-8')
        except UnicodeError:
            self.logger.warning("Unicode normalization issue, keeping original")
        
        return normalized
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text
        
        Args:
            text: Raw input text
            
        Returns:
            Cleaned text
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Normalize Unicode
        text = self.normalize_unicode(text)
        
        # Convert to lowercase for consistency (preserve case for NER later)
        original_text = text
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Log cleaning if significant changes
        if len(original_text) - len(text) > 10:
            self.logger.debug(f"Text cleaned: {len(original_text)} -> {len(text)} characters")
        
        return text
    
    def tokenize_text(self, text: str) -> List[str]:
        """
        Tokenize text using spaCy
        
        Args:
            text: Input text to tokenize
            
        Returns:
            List of tokens
        """
        try:
            doc = self.nlp(text)
            tokens = [token.text for token in doc if not token.is_space]
            return tokens
        except Exception as e:
            self.logger.error(f"Tokenization error: {str(e)}")
            # Fallback to simple splitting
            return text.split()
    
    def extract_sentences(self, text: str) -> List[str]:
        """
        Extract sentences using spaCy
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        try:
            doc = self.nlp(text)
            sentences = [sent.text.strip() for sent in doc.sents]
            return sentences
        except Exception as e:
            self.logger.error(f"Sentence extraction error: {str(e)}")
            # Fallback to simple splitting
            return text.split('.')
    
    def preprocess_for_ner(self, text: str) -> str:
        """
        Preprocess text specifically for NER model
        
        Args:
            text: Input text
            
        Returns:
            Preprocessed text suitable for NER
        """
        # Clean text but preserve case and punctuation for NER
        text = self.normalize_unicode(text)
        
        # Remove excessive whitespace but preserve sentence structure
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Ensure proper sentence endings for better NER
        if text and not text.endswith(('.', '!', '?')):
            text += '.'
        
        return text
    
    def preprocess_for_rules(self, text: str) -> str:
        """
        Preprocess text for rule-based extraction
        
        Args:
            text: Input text
            
        Returns:
            Preprocessed text suitable for regex patterns
        """
        # More aggressive cleaning for rule-based extraction
        text = self.clean_text(text)
        
        # Normalize common patterns
        text = self._normalize_patterns(text)
        
        return text
    
    def _normalize_patterns(self, text: str) -> str:
        """
        Normalize common patterns in text
        
        Args:
            text: Input text
            
        Returns:
            Text with normalized patterns
        """
        # Normalize currency symbols
        text = re.sub(r'[Rr]s\.?\s*', 'Rs ', text)
        text = re.sub(r'₹\s*', 'Rs ', text)
        
        # Normalize phone number patterns
        text = re.sub(r'[^\d\s+()-]', ' ', text)
        
        # Normalize date separators
        text = re.sub(r'[-/]', '-', text)
        
        return text
    
    def get_text_stats(self, text: str) -> Dict[str, int]:
        """
        Get basic statistics about the text
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with text statistics
        """
        stats = {
            'char_count': len(text),
            'word_count': len(text.split()),
            'sentence_count': len(self.extract_sentences(text)),
            'line_count': len(text.split('\n'))
        }
        
        # Add language detection
        languages = self.detect_languages(text)
        stats.update(languages)
        
        return stats
    
    def preprocess_inquiry(self, text: str) -> Dict[str, any]:
        """
        Main preprocessing method for customer inquiries
        
        Args:
            text: Raw inquiry text
            
        Returns:
            Dict containing preprocessed text and metadata
        """
        try:
            # Validate input
            if not text or len(text.strip()) < self.config.MIN_TEXT_LENGTH:
                return {
                    'cleaned_text': '',
                    'ner_text': '',
                    'rules_text': '',
                    'languages': {'english': False, 'hindi': False, 'hinglish': False},
                    'stats': {'char_count': 0, 'word_count': 0, 'sentence_count': 0, 'line_count': 0},
                    'status': 'TEXT_TOO_SHORT'
                }
            
            # Truncate if too long
            if len(text) > self.config.MAX_TEXT_LENGTH:
                text = text[:self.config.MAX_TEXT_LENGTH]
                self.logger.warning(f"Text truncated to {self.config.MAX_TEXT_LENGTH} characters")
            
            # Clean text
            cleaned_text = self.clean_text(text)
            
            # Preprocess for different extraction methods
            ner_text = self.preprocess_for_ner(cleaned_text)
            rules_text = self.preprocess_for_rules(cleaned_text)
            
            # Analyze text
            languages = self.detect_languages(text)
            stats = self.get_text_stats(cleaned_text)
            
            return {
                'cleaned_text': cleaned_text,
                'ner_text': ner_text,
                'rules_text': rules_text,
                'languages': languages,
                'stats': stats,
                'status': 'SUCCESS'
            }
            
        except Exception as e:
            self.logger.error(f"Preprocessing error: {str(e)}")
            return {
                'cleaned_text': text,
                'ner_text': text,
                'rules_text': text,
                'languages': {'english': False, 'hindi': False, 'hinglish': False},
                'stats': {'char_count': len(text), 'word_count': 0, 'sentence_count': 0, 'line_count': 0},
                'status': f'ERROR: {str(e)}'
            }

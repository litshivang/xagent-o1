"""
ML-based Entity Extraction Module
Uses BERT-based NER models for entity extraction from customer inquiries
"""

import re
from typing import Dict, List, Tuple, Optional, Any
import spacy
from spacy import displacy

from config import Config
from utils.logger import setup_logger

class MLExtractor:
    """ML-based entity extractor using spaCy NER models"""
    
    def __init__(self):
        self.config = Config()
        self.logger = setup_logger('ml_extractor')
        self.nlp = None
        self._load_model()
    
    def _load_model(self):
        """Load spaCy NER model"""
        try:
            self.logger.info(f"Loading spaCy NER model: {self.config.SPACY_MODEL}")
            
            # Load spaCy model with NER capabilities
            self.nlp = spacy.load(self.config.SPACY_MODEL)
            
            self.logger.info("spaCy NER model loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load spaCy model: {str(e)}")
            self.logger.warning("Falling back to basic entity extraction")
            try:
                from spacy.lang.en import English
                self.nlp = English()
            except:
                self.nlp = None
    
    def extract_entities_ner(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract entities using spaCy NER model
        
        Args:
            text: Input text for entity extraction
            
        Returns:
            List of extracted entities with metadata
        """
        entities = []
        
        if not self.nlp:
            self.logger.warning("spaCy NLP model not available, skipping ML extraction")
            return entities
        
        try:
            # Process text with spaCy
            doc = self.nlp(text)
            
            for ent in doc.ents:
                confidence = 0.8  # spaCy doesn't provide confidence scores by default
                if confidence >= self.config.NER_CONFIDENCE_THRESHOLD:
                    entities.append({
                        'text': ent.text,
                        'label': ent.label_,
                        'confidence': confidence,
                        'start': ent.start_char,
                        'end': ent.end_char,
                        'method': 'ML_NER'
                    })
            
            self.logger.debug(f"Extracted {len(entities)} entities using spaCy NER")
            
        except Exception as e:
            self.logger.error(f"spaCy NER extraction error: {str(e)}")
        
        return entities
    
    def extract_person_names(self, text: str) -> List[str]:
        """
        Extract person names from text
        
        Args:
            text: Input text
            
        Returns:
            List of person names
        """
        names = []
        entities = self.extract_entities_ner(text)
        
        for entity in entities:
            if entity['label'] in ['PERSON', 'PER']:
                names.append(entity['text'])
        
        # Additional pattern-based name extraction for Indian names
        names.extend(self._extract_indian_names(text))
        
        # Clean and deduplicate
        names = list(set([name.strip() for name in names if len(name.strip()) > 1]))
        
        return names
    
    def _extract_indian_names(self, text: str) -> List[str]:
        """
        Extract Indian names using patterns
        
        Args:
            text: Input text
            
        Returns:
            List of potential Indian names
        """
        names = []
        
        # Common Indian name patterns
        patterns = [
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # First Last
            r'\b[A-Z][a-z]+\s+[A-Z]\.\s*[A-Z][a-z]+\b',  # First M. Last
            r'\bMr\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # Mr. Name
            r'\bMs\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # Ms. Name
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            names.extend(matches)
        
        return names
    
    def extract_locations(self, text: str) -> List[str]:
        """
        Extract location entities
        
        Args:
            text: Input text
            
        Returns:
            List of locations
        """
        locations = []
        entities = self.extract_entities_ner(text)
        
        for entity in entities:
            if entity['label'] in ['GPE', 'LOC', 'LOCATION']:
                locations.append(entity['text'])
        
        # Check against known Indian destinations
        locations.extend(self._extract_indian_destinations(text))
        
        # Clean and deduplicate
        locations = list(set([loc.strip() for loc in locations if len(loc.strip()) > 1]))
        
        return locations
    
    def _extract_indian_destinations(self, text: str) -> List[str]:
        """
        Extract Indian destinations from text
        
        Args:
            text: Input text
            
        Returns:
            List of Indian destinations
        """
        destinations = []
        text_lower = text.lower()
        
        for destination in self.config.INDIAN_DESTINATIONS:
            if destination in text_lower:
                # Find the actual case in original text
                pattern = re.compile(re.escape(destination), re.IGNORECASE)
                matches = pattern.findall(text)
                if matches:
                    destinations.extend(matches)
        
        return destinations
    
    def extract_dates(self, text: str) -> List[str]:
        """
        Extract date entities
        
        Args:
            text: Input text
            
        Returns:
            List of dates
        """
        dates = []
        entities = self.extract_entities_ner(text)
        
        for entity in entities:
            if entity['label'] in ['DATE', 'TIME']:
                dates.append(entity['text'])
        
        return dates
    
    def extract_money(self, text: str) -> List[str]:
        """
        Extract monetary amounts
        
        Args:
            text: Input text
            
        Returns:
            List of monetary amounts
        """
        amounts = []
        entities = self.extract_entities_ner(text)
        
        for entity in entities:
            if entity['label'] in ['MONEY', 'MONETARY']:
                amounts.append(entity['text'])
        
        return amounts
    
    def extract_numbers(self, text: str) -> List[str]:
        """
        Extract numerical entities
        
        Args:
            text: Input text
            
        Returns:
            List of numbers
        """
        numbers = []
        entities = self.extract_entities_ner(text)
        
        for entity in entities:
            if entity['label'] in ['CARDINAL', 'NUMBER', 'QUANTITY']:
                numbers.append(entity['text'])
        
        return numbers
    
    def extract_all_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract all types of entities from text
        
        Args:
            text: Input text for extraction
            
        Returns:
            Dictionary with categorized entities
        """
        try:
            # Get all entities from NER
            entities = self.extract_entities_ner(text)
            
            # Categorize entities
            categorized = {
                'persons': [],
                'locations': [],
                'dates': [],
                'money': [],
                'numbers': [],
                'organizations': [],
                'miscellaneous': []
            }
            
            for entity in entities:
                label = entity['label'].upper()
                text_val = entity['text']
                
                if label in ['PERSON', 'PER']:
                    categorized['persons'].append(text_val)
                elif label in ['GPE', 'LOC', 'LOCATION']:
                    categorized['locations'].append(text_val)
                elif label in ['DATE', 'TIME']:
                    categorized['dates'].append(text_val)
                elif label in ['MONEY', 'MONETARY']:
                    categorized['money'].append(text_val)
                elif label in ['CARDINAL', 'NUMBER', 'QUANTITY']:
                    categorized['numbers'].append(text_val)
                elif label in ['ORG', 'ORGANIZATION']:
                    categorized['organizations'].append(text_val)
                else:
                    categorized['miscellaneous'].append(text_val)
            
            # Additional extractions
            categorized['persons'].extend(self._extract_indian_names(text))
            categorized['locations'].extend(self._extract_indian_destinations(text))
            
            # Clean and deduplicate all categories
            for category in categorized:
                categorized[category] = list(set([
                    item.strip() for item in categorized[category] 
                    if item and len(item.strip()) > 1
                ]))
            
            self.logger.debug(f"ML extraction completed: {len(entities)} total entities")
            
            return categorized
            
        except Exception as e:
            self.logger.error(f"ML entity extraction error: {str(e)}")
            return {
                'persons': [],
                'locations': [],
                'dates': [],
                'money': [],
                'numbers': [],
                'organizations': [],
                'miscellaneous': []
            }
    
    def get_extraction_confidence(self, entities: List[Dict[str, Any]]) -> float:
        """
        Calculate average confidence score for extracted entities
        
        Args:
            entities: List of entities with confidence scores
            
        Returns:
            Average confidence score
        """
        if not entities:
            return 0.0
        
        confidences = [entity.get('confidence', 0.0) for entity in entities]
        return sum(confidences) / len(confidences)

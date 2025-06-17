"""
Fusion Engine Module
Combines ML-based and rule-based extraction results with conflict resolution
"""

from typing import Dict, List, Any, Optional, Tuple
import re
from datetime import datetime
from difflib import SequenceMatcher

from config import Config
from utils.logger import setup_logger
from schema import TripInquiry

class FusionEngine:
    """Engine for fusing ML and rule-based extraction results"""
    
    def __init__(self):
        self.config = Config()
        self.logger = setup_logger('fusion_engine')
        
        # Confidence weights for different extraction methods
        self.method_weights = {
            'ML_NER': 0.7,
            'RULE_BASED': 0.3,
            'COMBINED': 1.0
        }
        
        # Similarity threshold for entity matching
        self.similarity_threshold = 0.8
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings
        
        Args:
            text1: First text string
            text2: Second text string
            
        Returns:
            Similarity score between 0 and 1
        """
        if not text1 or not text2:
            return 0.0
        
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def merge_lists(self, list1: List[str], list2: List[str]) -> List[str]:
        """
        Merge two lists removing duplicates and similar items
        
        Args:
            list1: First list
            list2: Second list
            
        Returns:
            Merged list with duplicates removed
        """
        merged = list(list1)  # Start with first list
        
        for item2 in list2:
            # Check if item2 is similar to any item in merged list
            is_similar = False
            for item1 in merged:
                if self.calculate_similarity(item1, item2) > self.similarity_threshold:
                    is_similar = True
                    break
            
            if not is_similar:
                merged.append(item2)
        
        return merged
    
    def resolve_names(self, ml_names: List[str], rule_names: List[str]) -> Tuple[List[str], str]:
        """
        Resolve person names from ML and rule-based extractions
        
        Args:
            ml_names: Names from ML extraction
            rule_names: Names from rule-based extraction
            
        Returns:
            Tuple of (resolved names, method used)
        """
        # If both methods found names, merge them
        if ml_names and rule_names:
            merged_names = self.merge_lists(ml_names, rule_names)
            return merged_names, 'COMBINED'
        
        # If only one method found names, use that
        if ml_names:
            return ml_names, 'ML_NER'
        elif rule_names:
            return rule_names, 'RULE_BASED'
        
        return [], 'NONE'
    
    def resolve_destinations(self, ml_locations: List[str], rule_destinations: List[str]) -> Tuple[List[str], str]:
        """
        Resolve destinations from ML and rule-based extractions
        
        Args:
            ml_locations: Locations from ML extraction
            rule_destinations: Destinations from rule-based extraction
            
        Returns:
            Tuple of (resolved destinations, method used)
        """
        # Filter ML locations to only include known destinations
        ml_destinations = []
        for location in ml_locations:
            if location.lower() in self.config.INDIAN_DESTINATIONS:
                ml_destinations.append(location)
        
        # Merge destinations
        if ml_destinations and rule_destinations:
            merged_destinations = self.merge_lists(ml_destinations, rule_destinations)
            return merged_destinations, 'COMBINED'
        elif ml_destinations:
            return ml_destinations, 'ML_NER'
        elif rule_destinations:
            return rule_destinations, 'RULE_BASED'
        
        return [], 'NONE'
    
    def resolve_dates(self, ml_dates: List[str], rule_dates: List[str]) -> Tuple[List[str], str]:
        """
        Resolve travel dates from ML and rule-based extractions
        
        Args:
            ml_dates: Dates from ML extraction
            rule_dates: Dates from rule-based extraction
            
        Returns:
            Tuple of (resolved dates, method used)
        """
        # Rule-based dates are generally more accurate for structured formats
        if rule_dates:
            # Validate and clean rule-based dates
            valid_dates = self._validate_dates(rule_dates)
            if valid_dates:
                return valid_dates, 'RULE_BASED'
        
        # Fallback to ML dates if available
        if ml_dates:
            valid_dates = self._validate_dates(ml_dates)
            if valid_dates:
                return valid_dates, 'ML_NER'
        
        # Combine if both have valid dates
        if ml_dates and rule_dates:
            all_dates = ml_dates + rule_dates
            valid_dates = self._validate_dates(all_dates)
            return valid_dates, 'COMBINED'
        
        return [], 'NONE'
    
    def _validate_dates(self, dates: List[str]) -> List[str]:
        """
        Validate and normalize date strings
        
        Args:
            dates: List of date strings
            
        Returns:
            List of valid date strings
        """
        valid_dates = []
        
        for date_str in dates:
            if self._is_valid_date(date_str):
                valid_dates.append(date_str.strip())
        
        return list(set(valid_dates))  # Remove duplicates
    
    def _is_valid_date(self, date_str: str) -> bool:
        """
        Check if a string represents a valid date
        
        Args:
            date_str: Date string to validate
            
        Returns:
            True if valid date, False otherwise
        """
        # Basic date validation patterns
        date_patterns = [
            r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',  # DD/MM/YYYY
            r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',    # YYYY/MM/DD
            r'\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)',  # DD Month
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, date_str, re.IGNORECASE):
                return True
        
        return False
    
    def resolve_budget(self, ml_money: List[str], rule_amounts: List[Dict[str, str]]) -> Tuple[List[str], str]:
        """
        Resolve budget information
        
        Args:
            ml_money: Money entities from ML extraction
            rule_amounts: Currency amounts from rule-based extraction
            
        Returns:
            Tuple of (resolved budget, method used)
        """
        budget_info = []
        
        # Process rule-based amounts (more structured)
        if rule_amounts:
            for amount_info in rule_amounts:
                budget_info.append(amount_info['amount'])
            return budget_info, 'RULE_BASED'
        
        # Fallback to ML money entities
        if ml_money:
            return ml_money, 'ML_NER'
        
        return [], 'NONE'
    
    def resolve_traveler_count(self, ml_numbers: List[str], rule_counts: List[str]) -> Tuple[str, str]:
        """
        Resolve number of travelers
        
        Args:
            ml_numbers: Numbers from ML extraction
            rule_counts: Traveler counts from rule-based extraction
            
        Returns:
            Tuple of (traveler count, method used)
        """
        # Rule-based counts are more accurate as they're contextual
        if rule_counts:
            # Take the first valid count
            for count in rule_counts:
                if count.isdigit() and 1 <= int(count) <= 50:  # Reasonable range
                    return count, 'RULE_BASED'
        
        # Check ML numbers for reasonable traveler counts
        if ml_numbers:
            for number in ml_numbers:
                if number.isdigit() and 1 <= int(number) <= 50:
                    return number, 'ML_NER'
        
        return '', 'NONE'
    
    def resolve_contact_info(self, ml_entities: Dict[str, List[str]], rule_contact: Dict[str, List[str]]) -> Tuple[Dict[str, List[str]], str]:
        """
        Resolve contact information
        
        Args:
            ml_entities: ML extracted entities
            rule_contact: Rule-based contact info
            
        Returns:
            Tuple of (contact info, method used)
        """
        contact_info = {
            'emails': [],
            'phones': []
        }
        
        # Rule-based contact info is generally more accurate
        if rule_contact.get('emails') or rule_contact.get('phones'):
            contact_info['emails'] = rule_contact.get('emails', [])
            contact_info['phones'] = rule_contact.get('phones', [])
            method = 'RULE_BASED'
        else:
            # No rule-based contact info found
            method = 'NONE'
        
        # Merge with any ML extracted emails (if any)
        # Note: BERT NER typically doesn't extract emails well
        
        return contact_info, method
    
    def fuse_extractions(self, ml_results: Dict[str, List[str]], rule_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main fusion method that combines ML and rule-based extraction results
        
        Args:
            ml_results: Results from ML-based extraction
            rule_results: Results from rule-based extraction
            
        Returns:
            Fused extraction results
        """
        try:
            self.logger.debug("Starting fusion of ML and rule-based extractions")
            
            # Resolve each entity type
            names, names_method = self.resolve_names(
                ml_results.get('persons', []),
                rule_results.get('names', [])
            )
            
            destinations, dest_method = self.resolve_destinations(
                ml_results.get('locations', []),
                rule_results.get('destinations', [])
            )
            
            dates, dates_method = self.resolve_dates(
                ml_results.get('dates', []),
                rule_results.get('dates', [])
            )
            
            budget, budget_method = self.resolve_budget(
                ml_results.get('money', []),
                rule_results.get('currency_amounts', [])
            )
            
            traveler_count, count_method = self.resolve_traveler_count(
                ml_results.get('numbers', []),
                rule_results.get('traveler_counts', [])
            )
            
            contact_info, contact_method = self.resolve_contact_info(
                ml_results,
                rule_results.get('contact_info', {})
            )
            
            # Create fused result
            fused_result = {
                'customer_name': ', '.join(names) if names else '',
                'travel_dates': ', '.join(dates) if dates else '',
                'destination': ', '.join(destinations) if destinations else '',
                'budget': ', '.join(budget) if budget else '',
                'travelers_count': traveler_count,
                'contact_info': self._format_contact_info(contact_info),
                'special_requirements': self._extract_special_requirements(rule_results),
                'extraction_methods': {
                    'names': names_method,
                    'destinations': dest_method,
                    'dates': dates_method,
                    'budget': budget_method,
                    'travelers_count': count_method,
                    'contact_info': contact_method
                },
                'confidence_score': self._calculate_confidence(
                    names_method, dest_method, dates_method, 
                    budget_method, count_method, contact_method
                )
            }
            
            self.logger.debug(f"Fusion completed with confidence: {fused_result['confidence_score']:.2f}")
            return fused_result
            
        except Exception as e:
            self.logger.error(f"Fusion error: {str(e)}")
            return self._create_empty_result()
    
    def _format_contact_info(self, contact_info: Dict[str, List[str]]) -> str:
        """
        Format contact information for display
        
        Args:
            contact_info: Dictionary with emails and phones
            
        Returns:
            Formatted contact string
        """
        contact_parts = []
        
        if contact_info.get('emails'):
            contact_parts.extend(contact_info['emails'])
        
        if contact_info.get('phones'):
            contact_parts.extend(contact_info['phones'])
        
        return ', '.join(contact_parts)
    
    def _extract_special_requirements(self, rule_results: Dict[str, Any]) -> str:
        """
        Extract special requirements from rule-based results
        
        Args:
            rule_results: Rule-based extraction results
            
        Returns:
            Special requirements string
        """
        requirements = []
        
        # Add duration information
        if rule_results.get('durations'):
            requirements.extend(rule_results['durations'])
        
        # Add any other special information
        # This could be extended to include hotel preferences, activities, etc.
        
        return ', '.join(requirements) if requirements else ''
    
    def _calculate_confidence(self, *methods) -> float:
        """
        Calculate overall confidence score based on extraction methods
        
        Args:
            *methods: Variable number of method strings
            
        Returns:
            Confidence score between 0 and 1
        """
        method_scores = []
        
        for method in methods:
            if method == 'COMBINED':
                method_scores.append(1.0)
            elif method == 'RULE_BASED':
                method_scores.append(0.8)
            elif method == 'ML_NER':
                method_scores.append(0.7)
            else:  # NONE
                method_scores.append(0.0)
        
        # Calculate weighted average
        if method_scores:
            return sum(method_scores) / len(method_scores)
        else:
            return 0.0
    
    def _create_empty_result(self) -> Dict[str, Any]:
        """
        Create empty fusion result for error cases
        
        Returns:
            Empty result dictionary
        """
        return {
            'customer_name': '',
            'travel_dates': '',
            'destination': '',
            'budget': '',
            'travelers_count': '',
            'contact_info': '',
            'special_requirements': '',
            'extraction_methods': {
                'names': 'NONE',
                'destinations': 'NONE',
                'dates': 'NONE',
                'budget': 'NONE',
                'travelers_count': 'NONE',
                'contact_info': 'NONE'
            },
            'confidence_score': 0.0
        }

    def validate_and_format_with_schema(self, fused_data: Dict[str, Any], file_name: str = "") -> Dict[str, Any]:
        """
        Validate and format extraction results using TripInquiry schema
        
        Args:
            fused_data: Fused extraction results
            file_name: Source file name
            
        Returns:
            Schema-validated and formatted data
        """
        try:
            # Extract schema-compatible data from fused results
            schema_data = self._map_to_schema_fields(fused_data, file_name)
            
            # Validate using Pydantic schema  
            trip_inquiry = TripInquiry(**schema_data)
            
            # Convert back to dict and merge with original extraction metadata
            validated_data = trip_inquiry.dict()
            validated_data['extraction_methods'] = fused_data.get('extraction_methods', {})
            validated_data['confidence_score'] = fused_data.get('confidence_score', 0.0)
            
            self.logger.debug(f"Schema validation successful for {file_name}")
            return validated_data
            
        except Exception as e:
            self.logger.warning(f"Schema validation failed for {file_name}: {str(e)}")
            # Return original data with validation status
            fused_data['schema_validation'] = 'failed'
            fused_data['validation_error'] = str(e)
            return fused_data
    
    def _map_to_schema_fields(self, fused_data: Dict[str, Any], file_name: str) -> Dict[str, Any]:
        """
        Map fused extraction results to TripInquiry schema fields
        
        Args:
            fused_data: Fused extraction results
            file_name: Source file name
            
        Returns:
            Dictionary with schema-compatible field mappings
        """
        # Parse traveler information
        travelers_info = self._parse_travelers_info(fused_data.get('travelers_count', ''))
        
        # Parse dates
        dates_info = self._parse_dates_info(fused_data.get('travel_dates', ''))
        
        # Parse destinations
        destinations = self._parse_destinations_list(fused_data.get('destination', ''))
        
        # Parse activities from special requirements
        activities = self._extract_activities(fused_data.get('special_requirements', ''))
        
        # Parse hotel and meal preferences
        hotel_prefs, meal_prefs = self._parse_preferences(fused_data.get('special_requirements', ''))
        
        # Parse flight requirements
        needs_flight = self._parse_flight_requirements(fused_data.get('special_requirements', ''))
        
        return {
            'num_travelers': travelers_info.get('total'),
            'num_adults': travelers_info.get('adults'),
            'num_children': travelers_info.get('children'),
            'destinations': destinations,
            'start_date': dates_info.get('start_date'),
            'end_date': dates_info.get('end_date'),
            'duration_nights': dates_info.get('nights'),
            'hotel_preferences': hotel_prefs,
            'meal_preferences': meal_prefs,
            'activities': activities,
            'needs_flight': needs_flight,
            'budget': fused_data.get('budget', ''),
            'special_requests': fused_data.get('special_requirements', ''),
            'customer_name': fused_data.get('customer_name', ''),
            'contact_info': fused_data.get('contact_info', ''),
            'file_name': file_name,
            'processing_status': 'completed',
            'extraction_method': self._get_primary_method(fused_data.get('extraction_methods', {}))
        }
    
    def _parse_travelers_info(self, travelers_text: str) -> Dict[str, Optional[int]]:
        """Parse traveler count information"""
        result: Dict[str, Optional[int]] = {'total': None, 'adults': None, 'children': None}
        
        if not travelers_text:
            return result
        
        # Extract total number
        total_match = re.search(r'(\d+)', travelers_text)
        if total_match:
            result['total'] = int(total_match.group(1))
        
        # Extract adults and children
        adult_match = re.search(r'(\d+)\s*adults?', travelers_text, re.IGNORECASE)
        if adult_match:
            result['adults'] = int(adult_match.group(1))
        
        child_match = re.search(r'(\d+)\s*(?:kid|child|children)', travelers_text, re.IGNORECASE)
        if child_match:
            result['children'] = int(child_match.group(1))
        
        return result
    
    def _parse_dates_info(self, dates_text: str) -> Dict[str, Optional[str]]:
        """Parse travel dates information"""
        result: Dict[str, Optional[str]] = {'start_date': None, 'end_date': None, 'nights': None}
        
        if not dates_text:
            return result
        
        # Extract nights duration
        nights_match = re.search(r'(\d+)\s*nights?', dates_text, re.IGNORECASE)
        if nights_match:
            result['nights'] = nights_match.group(1)
        
        return result
    
    def _parse_destinations_list(self, destinations_text: str) -> List[str]:
        """Parse destinations into a list"""
        if not destinations_text:
            return []
        
        # Split by common separators and clean
        destinations = re.split(r'[,;|]', destinations_text)
        return [dest.strip() for dest in destinations if dest.strip()]
    
    def _extract_activities(self, special_requirements: str) -> List[str]:
        """Extract activities from special requirements text"""
        if not special_requirements:
            return []
        
        # Common activity patterns from the sample data
        activities = []
        text_lower = special_requirements.lower()
        
        # Extract activities mentioned in the text
        common_activities = [
            'beach time', 'snorkeling', 'romantic dinner', 'desert safari',
            'city tour', 'night safari', 'cruise ride', 'sightseeing',
            'houseboat', 'james bond island', 'phi phi island',
            'bangkok city tour', 'safari world', 'sentosa', 'universal studios',
            'burj khalifa', 'dhow cruise', 'miracle garden', 'global village',
            'swiss alps', 'venice', 'paris', 'rome', 'kufri', 'solang valley',
            'mall road', 'hidimba temple', 'dal lake', 'gulmarg', 'sonmarg',
            'pahalgam', 'munnar', 'periyar', 'cochin', 'alleppey', 'fort aguada',
            'baga beach', 'dudhsagar falls', 'tanah lot', 'ubud tour',
            'nusa penida', 'kintamani'
        ]
        
        for activity in common_activities:
            if activity in text_lower:
                activities.append(activity.title())
        
        return activities
    
    def _parse_preferences(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse hotel and meal preferences"""
        hotel_pref = None
        meal_pref = None
        
        if not text:
            return hotel_pref, meal_pref
        
        text_lower = text.lower()
        
        # Hotel preferences
        if 'water villa' in text_lower:
            hotel_pref = 'water villa'
        elif 'luxury' in text_lower:
            hotel_pref = 'luxury'
        elif '4-star' in text_lower:
            hotel_pref = '4-star'
        elif '3-star' in text_lower:
            hotel_pref = '3-star'
        elif 'budget' in text_lower:
            hotel_pref = 'budget'
        
        # Meal preferences
        if 'all meals' in text_lower:
            meal_pref = 'all meals'
        elif 'breakfast and dinner' in text_lower:
            meal_pref = 'breakfast and dinner'
        elif 'breakfast only' in text_lower:
            meal_pref = 'breakfast only'
        elif 'veg meals' in text_lower:
            meal_pref = 'veg meals'
        
        return hotel_pref, meal_pref
    
    def _parse_flight_requirements(self, text: str) -> Optional[bool]:
        """Parse flight requirements"""
        if not text:
            return None
        
        text_lower = text.lower()
        if 'flights required' in text_lower or 'flights needed' in text_lower:
            return True
        elif 'flights not required' in text_lower or 'flights not needed' in text_lower:
            return False
        
        return None
    
    def _get_primary_method(self, extraction_methods: Dict[str, str]) -> str:
        """Get primary extraction method used"""
        if not extraction_methods:
            return 'unknown'
        
        # Count method usage
        method_counts = {}
        for method in extraction_methods.values():
            method_counts[method] = method_counts.get(method, 0) + 1
        
        # Return most used method
        if method_counts:
            return max(method_counts.items(), key=lambda x: x[1])[0]
        
        return 'unknown'

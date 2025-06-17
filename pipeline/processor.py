"""
Main Processing Pipeline
Orchestrates the entire inquiry processing workflow
"""

import time
from typing import Dict, Any, Optional
from pathlib import Path

from config import Config
from utils.logger import setup_logger
from modules.text_preprocessor import TextPreprocessor
from modules.ml_extractor import MLExtractor
from modules.rule_extractor import RuleExtractor
from modules.fusion_engine import FusionEngine

class InquiryProcessor:
    """Main processor that orchestrates the entire inquiry processing pipeline"""
    
    def __init__(self):
        self.config = Config()
        self.logger = setup_logger('inquiry_processor')
        
        # Initialize all processing modules
        self.text_preprocessor = TextPreprocessor()
        self.ml_extractor = MLExtractor()
        self.rule_extractor = RuleExtractor()
        self.fusion_engine = FusionEngine()
        
        self.logger.info("Inquiry processor initialized successfully")
    
    def process_inquiry(self, text_content: str, file_path: str) -> Dict[str, Any]:
        """
        Process a single customer inquiry through the complete pipeline
        
        Args:
            text_content: Raw text content of the inquiry
            file_path: Path to the source file
            
        Returns:
            Dictionary containing extracted information and metadata
        """
        start_time = time.time()
        
        try:
            self.logger.debug(f"Starting processing pipeline for: {file_path}")
            
            # Step 1: Text Preprocessing
            preprocessing_start = time.time()
            preprocessed_data = self.text_preprocessor.preprocess_inquiry(text_content)
            
            if preprocessed_data['status'] != 'SUCCESS':
                self.logger.warning(f"Preprocessing failed for {file_path}: {preprocessed_data['status']}")
                return self._create_failed_result(file_path, preprocessed_data['status'], start_time)
            
            preprocessing_time = time.time() - preprocessing_start
            self.logger.debug(f"Preprocessing completed in {preprocessing_time:.3f}s")
            
            # Step 2: ML-based Entity Extraction
            ml_start = time.time()
            ml_results = self.ml_extractor.extract_all_entities(preprocessed_data['ner_text'])
            ml_time = time.time() - ml_start
            self.logger.debug(f"ML extraction completed in {ml_time:.3f}s")
            
            # Step 3: Rule-based Entity Extraction
            rule_start = time.time()
            rule_results = self.rule_extractor.extract_all_entities(preprocessed_data['rules_text'])
            rule_time = time.time() - rule_start
            self.logger.debug(f"Rule-based extraction completed in {rule_time:.3f}s")
            
            # Step 4: Fusion of Results
            fusion_start = time.time()
            fused_results = self.fusion_engine.fuse_extractions(ml_results, rule_results)
            fusion_time = time.time() - fusion_start
            self.logger.debug(f"Fusion completed in {fusion_time:.3f}s")
            
            # Step 5: Create Final Result
            total_processing_time = time.time() - start_time
            
            final_result = {
                'file_path': file_path,
                'customer_name': fused_results['customer_name'],
                'travel_dates': fused_results['travel_dates'],
                'destination': fused_results['destination'],
                'budget': fused_results['budget'],
                'travelers_count': fused_results['travelers_count'],
                'contact_info': fused_results['contact_info'],
                'special_requirements': fused_results['special_requirements'],
                'status': 'SUCCESS',
                'processing_time': total_processing_time,
                'confidence_score': fused_results['confidence_score'],
                'extraction_methods': fused_results['extraction_methods'],
                'pipeline_stats': {
                    'preprocessing_time': preprocessing_time,
                    'ml_extraction_time': ml_time,
                    'rule_extraction_time': rule_time,
                    'fusion_time': fusion_time,
                    'total_time': total_processing_time
                },
                'text_stats': preprocessed_data['stats'],
                'language_info': preprocessed_data['languages']
            }
            
            self.logger.info(f"Successfully processed {Path(file_path).name} in {total_processing_time:.3f}s")
            return final_result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Processing pipeline error: {str(e)}"
            self.logger.error(f"Error processing {file_path}: {error_msg}")
            
            return self._create_failed_result(file_path, f"ERROR: {error_msg}", start_time)
    
    def _create_failed_result(self, file_path: str, error_status: str, start_time: float) -> Dict[str, Any]:
        """
        Create a result structure for failed processing
        
        Args:
            file_path: Path to the source file
            error_status: Error status message
            start_time: Processing start time
            
        Returns:
            Failed result dictionary
        """
        processing_time = time.time() - start_time
        
        return {
            'file_path': file_path,
            'customer_name': '',
            'travel_dates': '',
            'destination': '',
            'budget': '',
            'travelers_count': '',
            'contact_info': '',
            'special_requirements': '',
            'status': error_status,
            'processing_time': processing_time,
            'confidence_score': 0.0,
            'extraction_methods': {
                'names': 'NONE',
                'destinations': 'NONE',
                'dates': 'NONE',
                'budget': 'NONE',
                'travelers_count': 'NONE',
                'contact_info': 'NONE'
            },
            'pipeline_stats': {
                'preprocessing_time': 0.0,
                'ml_extraction_time': 0.0,
                'rule_extraction_time': 0.0,
                'fusion_time': 0.0,
                'total_time': processing_time
            },
            'text_stats': {'char_count': 0, 'word_count': 0, 'sentence_count': 0, 'line_count': 0},
            'language_info': {'english': False, 'hindi': False, 'hinglish': False}
        }
    
    def validate_processing_result(self, result: Dict[str, Any]) -> bool:
        """
        Validate that a processing result has the expected structure
        
        Args:
            result: Processing result to validate
            
        Returns:
            True if result is valid, False otherwise
        """
        required_fields = [
            'file_path', 'customer_name', 'travel_dates', 'destination',
            'budget', 'travelers_count', 'contact_info', 'special_requirements',
            'status', 'processing_time', 'confidence_score'
        ]
        
        try:
            # Check required fields
            for field in required_fields:
                if field not in result:
                    self.logger.error(f"Missing required field in result: {field}")
                    return False
            
            # Check data types
            if not isinstance(result['processing_time'], (int, float)):
                self.logger.error("Processing time must be numeric")
                return False
            
            if not isinstance(result['confidence_score'], (int, float)):
                self.logger.error("Confidence score must be numeric")
                return False
            
            # Check confidence score range
            if not (0.0 <= result['confidence_score'] <= 1.0):
                self.logger.warning(f"Confidence score out of range: {result['confidence_score']}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Result validation error: {str(e)}")
            return False
    
    def get_processing_stats(self, results: list) -> Dict[str, Any]:
        """
        Calculate processing statistics from a list of results
        
        Args:
            results: List of processing results
            
        Returns:
            Dictionary with processing statistics
        """
        if not results:
            return {}
        
        try:
            # Basic counts
            total_files = len(results)
            successful = sum(1 for r in results if r['status'] == 'SUCCESS')
            failed = total_files - successful
            
            # Time statistics
            processing_times = [r['processing_time'] for r in results]
            total_time = sum(processing_times)
            avg_time = total_time / total_files
            min_time = min(processing_times)
            max_time = max(processing_times)
            
            # Confidence statistics (only for successful results)
            successful_results = [r for r in results if r['status'] == 'SUCCESS']
            if successful_results:
                confidence_scores = [r['confidence_score'] for r in successful_results]
                avg_confidence = sum(confidence_scores) / len(confidence_scores)
                min_confidence = min(confidence_scores)
                max_confidence = max(confidence_scores)
            else:
                avg_confidence = min_confidence = max_confidence = 0.0
            
            # Language distribution
            language_counts = {'english': 0, 'hindi': 0, 'hinglish': 0}
            for result in results:
                lang_info = result.get('language_info', {})
                for lang in language_counts:
                    if lang_info.get(lang, False):
                        language_counts[lang] += 1
            
            # Extraction method statistics
            method_counts = {}
            for result in successful_results:
                methods = result.get('extraction_methods', {})
                for entity_type, method in methods.items():
                    if method not in method_counts:
                        method_counts[method] = 0
                    method_counts[method] += 1
            
            stats = {
                'total_files': total_files,
                'successful': successful,
                'failed': failed,
                'success_rate': (successful / total_files) * 100,
                'processing_time': {
                    'total': total_time,
                    'average': avg_time,
                    'minimum': min_time,
                    'maximum': max_time
                },
                'confidence_scores': {
                    'average': avg_confidence,
                    'minimum': min_confidence,
                    'maximum': max_confidence
                },
                'language_distribution': language_counts,
                'extraction_methods': method_counts,
                'performance_metrics': {
                    'files_per_second': total_files / total_time if total_time > 0 else 0,
                    'meets_target': total_time <= self.config.TARGET_PROCESSING_TIME
                }
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error calculating processing stats: {str(e)}")
            return {}
    
    def optimize_processing_order(self, file_paths: list) -> list:
        """
        Optimize the order of file processing for better performance
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            Optimized list of file paths
        """
        try:
            # Get file sizes
            file_info = []
            for file_path in file_paths:
                try:
                    size = Path(file_path).stat().st_size
                    file_info.append((file_path, size))
                except:
                    file_info.append((file_path, 0))
            
            # Sort by size (process smaller files first for better parallel utilization)
            file_info.sort(key=lambda x: x[1])
            
            optimized_paths = [info[0] for info in file_info]
            
            self.logger.debug(f"Optimized processing order for {len(optimized_paths)} files")
            return optimized_paths
            
        except Exception as e:
            self.logger.error(f"Error optimizing processing order: {str(e)}")
            return file_paths  # Return original order if optimization fails
    
    def health_check(self) -> Dict[str, bool]:
        """
        Perform health check on all pipeline components
        
        Returns:
            Dictionary with health status of each component
        """
        health_status = {}
        
        try:
            # Check text preprocessor
            test_text = "Hello, this is a test."
            preprocessed = self.text_preprocessor.preprocess_inquiry(test_text)
            health_status['text_preprocessor'] = preprocessed['status'] == 'SUCCESS'
            
            # Check ML extractor
            try:
                ml_results = self.ml_extractor.extract_all_entities(test_text)
                health_status['ml_extractor'] = isinstance(ml_results, dict)
            except:
                health_status['ml_extractor'] = False
            
            # Check rule extractor
            try:
                rule_results = self.rule_extractor.extract_all_entities(test_text)
                health_status['rule_extractor'] = isinstance(rule_results, dict)
            except:
                health_status['rule_extractor'] = False
            
            # Check fusion engine
            try:
                test_ml = {'persons': ['Test'], 'locations': [], 'dates': [], 'money': [], 'numbers': []}
                test_rules = {'names': ['Test'], 'destinations': [], 'dates': [], 'currency_amounts': [], 'traveler_counts': [], 'contact_info': {'emails': [], 'phones': []}}
                fused = self.fusion_engine.fuse_extractions(test_ml, test_rules)
                health_status['fusion_engine'] = isinstance(fused, dict)
            except:
                health_status['fusion_engine'] = False
            
            # Overall status
            health_status['overall'] = all(health_status.values())
            
            self.logger.info(f"Health check completed: {health_status}")
            
        except Exception as e:
            self.logger.error(f"Health check error: {str(e)}")
            health_status['overall'] = False
        
        return health_status

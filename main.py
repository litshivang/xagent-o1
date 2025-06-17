#!/usr/bin/env python3
"""
AI Travel Agent - Main Entry Point
Processes customer inquiries using hybrid ML/rule-based extraction and generates Excel reports.
"""

import os
import sys
import time
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

# Add project root to Python path
sys.path.append(str(Path(__file__).parent))

from config import Config
from utils.logger import setup_logger
from utils.file_handler import FileHandler
from pipeline.processor import InquiryProcessor
from modules.excel_generator import ExcelGenerator

class TravelAgentApp:
    """Main application class for AI Travel Agent"""
    
    def __init__(self):
        self.config = Config()
        self.logger = setup_logger('travel_agent_main')
        self.file_handler = FileHandler()
        self.processor = InquiryProcessor()
        self.excel_generator = ExcelGenerator()
        
    def setup_directories(self):
        """Create necessary directories if they don't exist"""
        directories = [
            self.config.INQUIRIES_DIR,
            self.config.OUTPUT_DIR,
            self.config.LOGS_DIR
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            self.logger.info(f"Directory ensured: {directory}")
    
    def process_single_inquiry(self, file_path: str) -> Dict[str, Any]:
        """
        Process a single inquiry file
        
        Args:
            file_path: Path to the inquiry file
            
        Returns:
            Dict containing extracted information
        """
        try:
            self.logger.info(f"Processing inquiry: {file_path}")
            
            # Read file content
            content = self.file_handler.read_text_file(file_path)
            if not content:
                self.logger.warning(f"Empty or unreadable file: {file_path}")
                return self._create_empty_result(file_path)
            
            # Process the inquiry
            result = self.processor.process_inquiry(content, file_path)
            
            self.logger.info(f"Successfully processed: {file_path}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing {file_path}: {str(e)}")
            return self._create_error_result(file_path, str(e))
    
    def _create_empty_result(self, file_path: str) -> Dict[str, Any]:
        """Create empty result structure for failed processing"""
        return {
            'file_path': file_path,
            'customer_name': '',
            'travel_dates': '',
            'destination': '',
            'budget': '',
            'travelers_count': '',
            'contact_info': '',
            'special_requirements': '',
            'status': 'EMPTY_FILE',
            'processing_time': 0.0
        }
    
    def _create_error_result(self, file_path: str, error: str) -> Dict[str, Any]:
        """Create error result structure for failed processing"""
        return {
            'file_path': file_path,
            'customer_name': '',
            'travel_dates': '',
            'destination': '',
            'budget': '',
            'travelers_count': '',
            'contact_info': '',
            'special_requirements': '',
            'status': f'ERROR: {error}',
            'processing_time': 0.0
        }
    
    def process_inquiries_parallel(self, inquiry_files: List[str]) -> List[Dict[str, Any]]:
        """
        Process multiple inquiries in parallel
        
        Args:
            inquiry_files: List of file paths to process
            
        Returns:
            List of processing results
        """
        results = []
        
        self.logger.info(f"Starting parallel processing of {len(inquiry_files)} inquiries")
        start_time = time.time()
        
        # Use ThreadPoolExecutor for I/O bound tasks
        with ThreadPoolExecutor(max_workers=self.config.MAX_WORKERS) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self.process_single_inquiry, file_path): file_path
                for file_path in inquiry_files
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result(timeout=self.config.TASK_TIMEOUT)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Task failed for {file_path}: {str(e)}")
                    results.append(self._create_error_result(file_path, str(e)))
        
        processing_time = time.time() - start_time
        self.logger.info(f"Parallel processing completed in {processing_time:.2f} seconds")
        
        return results
    
    def run(self, inquiries_dir: str = None, output_file: str = None) -> str:
        """
        Main execution method
        
        Args:
            inquiries_dir: Directory containing inquiry files (optional)
            output_file: Output Excel file path (optional)
            
        Returns:
            Path to generated Excel file
        """
        try:
            # Setup directories
            self.setup_directories()
            
            # Use provided directories or defaults
            inquiries_dir = inquiries_dir or self.config.INQUIRIES_DIR
            output_file = output_file or self.config.DEFAULT_OUTPUT_FILE
            
            self.logger.info("=== AI Travel Agent Processing Started ===")
            start_time = time.time()
            
            # Get inquiry files
            inquiry_files = self.file_handler.get_text_files(inquiries_dir)
            
            if not inquiry_files:
                self.logger.warning(f"No inquiry files found in {inquiries_dir}")
                self.logger.info("Creating sample inquiry files for demonstration...")
                self._create_sample_inquiries(inquiries_dir)
                inquiry_files = self.file_handler.get_text_files(inquiries_dir)
            
            self.logger.info(f"Found {len(inquiry_files)} inquiry files to process")
            
            # Process inquiries in parallel
            results = self.process_inquiries_parallel(inquiry_files)
            
            # Generate Excel report
            self.logger.info("Generating Excel report...")
            excel_path = self.excel_generator.generate_report(results, output_file)
            
            total_time = time.time() - start_time
            self.logger.info(f"=== Processing completed in {total_time:.2f} seconds ===")
            self.logger.info(f"Excel report generated: {excel_path}")
            
            # Print summary
            self._print_summary(results, total_time)
            
            return excel_path
            
        except Exception as e:
            self.logger.error(f"Application error: {str(e)}")
            raise
    
    def _create_sample_inquiries(self, inquiries_dir: str):
        """Create sample inquiry files for demonstration"""
        sample_inquiries = [
            "Hi, I'm Rajesh Kumar and I want to plan a trip to Goa for 2 people from 15th December to 20th December. My budget is around Rs 50,000. Please help me with hotel bookings and sightseeing options. My contact is rajesh.kumar@email.com",
            
            "Hello! My name is Priya Sharma. मैं अपने family के साथ Kerala जाना चाहती हूं। We are 4 people total. Budget है approximately 1 lakh rupees. Travel dates: 5th January to 12th January. Need accommodation and transport arrangements. Contact: 9876543210",
            
            "Good morning, I am planning a honeymoon trip to Manali for me and my wife. Duration: 7 days starting from 25th February. Budget constraint: 75,000 INR. Looking for romantic destinations and good hotels. Name: Amit Gupta, Email: amit.gupta@gmail.com",
            
            "Namaste! Family trip plan kar raha hu for Rajasthan. 6 लोग हैं total including 2 children. March 10 se March 18 tak. Budget around 2 lakhs. Jaipur, Udaipur, Jodhpur cover karna hai. Contact: deepak.singh@yahoo.com, Phone: 8765432109",
            
            "Hi there! I'm Sarah Johnson, planning a solo backpacking trip across Himachal Pradesh. Duration: 3 weeks starting April 1st. Budget is flexible around $1500 USD. Looking for adventure activities and budget stays. Contact: sarah.j.traveler@gmail.com"
        ]
        
        for i, inquiry in enumerate(sample_inquiries, 1):
            file_path = os.path.join(inquiries_dir, f"inquiry_{i:03d}.txt")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(inquiry)
        
        self.logger.info(f"Created {len(sample_inquiries)} sample inquiry files")
    
    def _print_summary(self, results: List[Dict[str, Any]], total_time: float):
        """Print processing summary"""
        total_files = len(results)
        successful = sum(1 for r in results if not r['status'].startswith('ERROR'))
        errors = total_files - successful
        
        print("\n" + "="*60)
        print("           AI TRAVEL AGENT - PROCESSING SUMMARY")
        print("="*60)
        print(f"Total Files Processed: {total_files}")
        print(f"Successful: {successful}")
        print(f"Errors: {errors}")
        print(f"Total Processing Time: {total_time:.2f} seconds")
        print(f"Average Time per File: {total_time/total_files:.3f} seconds")
        print("="*60)
        
        if errors > 0:
            print("\nFiles with errors:")
            for result in results:
                if result['status'].startswith('ERROR'):
                    print(f"  - {os.path.basename(result['file_path'])}: {result['status']}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='AI Travel Agent - Process customer inquiries')
    parser.add_argument('--inquiries-dir', '-i', 
                       help='Directory containing inquiry files',
                       default=None)
    parser.add_argument('--output-file', '-o',
                       help='Output Excel file path',
                       default=None)
    parser.add_argument('--verbose', '-v',
                       action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    try:
        # Create and run the application
        app = TravelAgentApp()
        excel_path = app.run(args.inquiries_dir, args.output_file)
        
        print(f"\n✅ Processing completed successfully!")
        print(f"📊 Excel report generated: {excel_path}")
        
    except KeyboardInterrupt:
        print("\n❌ Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Application error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

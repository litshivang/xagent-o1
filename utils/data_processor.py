"""
Data Processing Utilities for AI Travel Agent
Handles conversion of bulk data files into individual inquiry files
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DataProcessor:
    """Processes bulk inquiry data files into individual inquiry files"""
    
    def __init__(self, sample_data_dir: str = "sample_data"):
        self.sample_data_dir = Path(sample_data_dir)
        self.sample_data_dir.mkdir(exist_ok=True)
        
    def extract_inquiries_from_file(self, file_path: str, language: str) -> List[Dict[str, Any]]:
        """
        Extract individual inquiries from a bulk file
        
        Args:
            file_path: Path to the bulk file
            language: Language identifier (hindi, english, hinglish, hindi_english)
            
        Returns:
            List of inquiry dictionaries
        """
        inquiries = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split by separator patterns
            if language == 'hindi':
                # Hindi emails separated by ---
                sections = re.split(r'\n---\n', content)
            elif language == 'english':
                # English emails separated by ---
                sections = re.split(r'\n---\n', content)
            elif language == 'hinglish':
                # Hinglish emails separated by ---
                sections = re.split(r'\n---\n', content)
            elif language == 'hindi_english':
                # Hindi-English mix emails separated by ---
                sections = re.split(r'\n---\n', content)
            else:
                sections = re.split(r'\n---\n', content)
            
            for i, section in enumerate(sections):
                section = section.strip()
                if section and len(section) > 50:  # Filter out very short sections
                    inquiries.append({
                        'content': section,
                        'language': language,
                        'sequence': i + 1
                    })
                    
            logger.info(f"Extracted {len(inquiries)} inquiries from {file_path}")
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            
        return inquiries
    
    def create_individual_files(self, inquiries: List[Dict[str, Any]], language: str) -> List[str]:
        """
        Create individual inquiry files from extracted data
        
        Args:
            inquiries: List of inquiry dictionaries
            language: Language identifier
            
        Returns:
            List of created file paths
        """
        created_files = []
        
        for inquiry in inquiries:
            # Create filename with language prefix and sequence number
            filename = f"{language}_{inquiry['sequence']:03d}.txt"
            file_path = self.sample_data_dir / filename
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(inquiry['content'])
                
                created_files.append(str(file_path))
                
            except Exception as e:
                logger.error(f"Error creating file {file_path}: {str(e)}")
        
        logger.info(f"Created {len(created_files)} files for {language}")
        return created_files
    
    def process_bulk_files(self, file_mappings: Dict[str, str]) -> Dict[str, List[str]]:
        """
        Process all bulk files and create individual inquiry files
        
        Args:
            file_mappings: Dictionary mapping language to file path
            
        Returns:
            Dictionary mapping language to list of created files
        """
        all_created_files = {}
        
        for language, file_path in file_mappings.items():
            if os.path.exists(file_path):
                logger.info(f"Processing {language} file: {file_path}")
                inquiries = self.extract_inquiries_from_file(file_path, language)
                created_files = self.create_individual_files(inquiries, language)
                all_created_files[language] = created_files
            else:
                logger.warning(f"File not found: {file_path}")
                all_created_files[language] = []
        
        total_files = sum(len(files) for files in all_created_files.values())
        logger.info(f"Total files created: {total_files}")
        
        return all_created_files
    
    def get_all_inquiry_files(self) -> List[str]:
        """
        Get list of all inquiry files in the sample data directory
        
        Returns:
            List of file paths
        """
        inquiry_files = []
        
        for file_path in self.sample_data_dir.glob("*.txt"):
            inquiry_files.append(str(file_path))
        
        inquiry_files.sort()  # Sort for consistent processing order
        return inquiry_files
"""
File handling utilities for AI Travel Agent
Handles file I/O operations for customer inquiries
"""

import os
import glob
from pathlib import Path
from typing import List, Optional, Dict, Any
import chardet

from config import Config
from utils.logger import setup_logger

class FileHandler:
    """Handles file operations for customer inquiry processing"""
    
    def __init__(self):
        self.config = Config()
        self.logger = setup_logger('file_handler')
        
        # Supported text file extensions
        self.text_extensions = ['.txt', '.text', '.md', '.rtf']
        
        # Encoding detection settings
        self.encoding_confidence_threshold = 0.7
    
    def detect_encoding(self, file_path: str) -> str:
        """
        Detect file encoding using chardet
        
        Args:
            file_path: Path to the file
            
        Returns:
            Detected encoding or UTF-8 as fallback
        """
        try:
            with open(file_path, 'rb') as file:
                raw_data = file.read(10000)  # Read first 10KB for detection
                
            result = chardet.detect(raw_data)
            
            if result['confidence'] >= self.encoding_confidence_threshold:
                encoding = result['encoding']
                self.logger.debug(f"Detected encoding for {file_path}: {encoding} (confidence: {result['confidence']:.2f})")
                return encoding
            else:
                self.logger.warning(f"Low confidence encoding detection for {file_path}, using UTF-8")
                return 'utf-8'
                
        except Exception as e:
            self.logger.error(f"Encoding detection error for {file_path}: {str(e)}")
            return 'utf-8'
    
    def read_text_file(self, file_path: str) -> Optional[str]:
        """
        Read text file with automatic encoding detection
        
        Args:
            file_path: Path to the text file
            
        Returns:
            File content as string or None if error
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                self.logger.error(f"File not found: {file_path}")
                return None
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                self.logger.warning(f"Empty file: {file_path}")
                return ""
            
            if file_size > self.config.MAX_TEXT_LENGTH * 2:  # Rough estimate
                self.logger.warning(f"Large file detected: {file_path} ({file_size} bytes)")
            
            # Detect encoding
            encoding = self.detect_encoding(file_path)
            
            # Read file content
            with open(file_path, 'r', encoding=encoding, errors='replace') as file:
                content = file.read()
            
            self.logger.debug(f"Successfully read file: {file_path} ({len(content)} characters)")
            return content
            
        except UnicodeDecodeError as e:
            self.logger.error(f"Unicode decode error for {file_path}: {str(e)}")
            # Try with different encodings
            for fallback_encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    with open(file_path, 'r', encoding=fallback_encoding, errors='replace') as file:
                        content = file.read()
                    self.logger.warning(f"Successfully read {file_path} with fallback encoding: {fallback_encoding}")
                    return content
                except:
                    continue
            
            self.logger.error(f"Failed to read {file_path} with any encoding")
            return None
            
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {str(e)}")
            return None
    
    def get_text_files(self, directory: str) -> List[str]:
        """
        Get all text files from a directory
        
        Args:
            directory: Directory path to search
            
        Returns:
            List of text file paths
        """
        text_files = []
        
        try:
            if not os.path.exists(directory):
                self.logger.error(f"Directory not found: {directory}")
                return text_files
            
            if not os.path.isdir(directory):
                self.logger.error(f"Path is not a directory: {directory}")
                return text_files
            
            # Search for text files
            for extension in self.text_extensions:
                pattern = os.path.join(directory, f"*{extension}")
                files = glob.glob(pattern)
                text_files.extend(files)
            
            # Also include files without extension that might be text
            for file_path in glob.glob(os.path.join(directory, "*")):
                if os.path.isfile(file_path) and not os.path.splitext(file_path)[1]:
                    # Check if it's a text file by trying to read it
                    if self._is_text_file(file_path):
                        text_files.append(file_path)
            
            # Sort files for consistent processing order
            text_files.sort()
            
            self.logger.info(f"Found {len(text_files)} text files in {directory}")
            return text_files
            
        except Exception as e:
            self.logger.error(f"Error getting text files from {directory}: {str(e)}")
            return []
    
    def _is_text_file(self, file_path: str) -> bool:
        """
        Check if a file is a text file by examining its content
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file appears to be text, False otherwise
        """
        try:
            with open(file_path, 'rb') as file:
                chunk = file.read(1024)  # Read first 1KB
            
            # Check for null bytes (binary files usually contain them)
            if b'\x00' in chunk:
                return False
            
            # Try to decode as text
            try:
                chunk.decode('utf-8')
                return True
            except UnicodeDecodeError:
                try:
                    chunk.decode('latin-1')
                    return True
                except UnicodeDecodeError:
                    return False
                    
        except Exception:
            return False
    
    def write_text_file(self, file_path: str, content: str, encoding: str = 'utf-8') -> bool:
        """
        Write content to a text file
        
        Args:
            file_path: Path to the output file
            content: Content to write
            encoding: File encoding (default: utf-8)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write file
            with open(file_path, 'w', encoding=encoding) as file:
                file.write(content)
            
            self.logger.debug(f"Successfully wrote file: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error writing file {file_path}: {str(e)}")
            return False
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get information about a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        try:
            if not os.path.exists(file_path):
                return {'exists': False}
            
            stat = os.stat(file_path)
            
            return {
                'exists': True,
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'created': stat.st_ctime,
                'is_file': os.path.isfile(file_path),
                'is_dir': os.path.isdir(file_path),
                'extension': os.path.splitext(file_path)[1].lower(),
                'basename': os.path.basename(file_path),
                'dirname': os.path.dirname(file_path)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting file info for {file_path}: {str(e)}")
            return {'exists': False, 'error': str(e)}
    
    def validate_directory(self, directory: str, create_if_missing: bool = False) -> bool:
        """
        Validate that a directory exists and is accessible
        
        Args:
            directory: Directory path to validate
            create_if_missing: Create directory if it doesn't exist
            
        Returns:
            True if directory is valid, False otherwise
        """
        try:
            if os.path.exists(directory):
                if not os.path.isdir(directory):
                    self.logger.error(f"Path exists but is not a directory: {directory}")
                    return False
                
                # Check read/write permissions
                if not os.access(directory, os.R_OK):
                    self.logger.error(f"Directory not readable: {directory}")
                    return False
                
                if not os.access(directory, os.W_OK):
                    self.logger.warning(f"Directory not writable: {directory}")
                
                return True
            
            elif create_if_missing:
                os.makedirs(directory, exist_ok=True)
                self.logger.info(f"Created directory: {directory}")
                return True
            
            else:
                self.logger.error(f"Directory does not exist: {directory}")
                return False
                
        except Exception as e:
            self.logger.error(f"Directory validation error for {directory}: {str(e)}")
            return False
    
    def cleanup_temp_files(self, directory: str, pattern: str = "*.tmp") -> int:
        """
        Clean up temporary files in a directory
        
        Args:
            directory: Directory to clean
            pattern: File pattern to match (default: *.tmp)
            
        Returns:
            Number of files deleted
        """
        deleted_count = 0
        
        try:
            if not os.path.exists(directory):
                return deleted_count
            
            temp_files = glob.glob(os.path.join(directory, pattern))
            
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                    deleted_count += 1
                    self.logger.debug(f"Deleted temp file: {temp_file}")
                except Exception as e:
                    self.logger.warning(f"Could not delete temp file {temp_file}: {str(e)}")
            
            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} temporary files from {directory}")
            
        except Exception as e:
            self.logger.error(f"Cleanup error in {directory}: {str(e)}")
        
        return deleted_count
    
    def get_directory_stats(self, directory: str) -> Dict[str, Any]:
        """
        Get statistics about files in a directory
        
        Args:
            directory: Directory to analyze
            
        Returns:
            Dictionary with directory statistics
        """
        stats = {
            'total_files': 0,
            'text_files': 0,
            'total_size': 0,
            'extensions': {},
            'largest_file': {'name': '', 'size': 0},
            'smallest_file': {'name': '', 'size': float('inf')}
        }
        
        try:
            if not os.path.exists(directory):
                return stats
            
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    try:
                        file_size = os.path.getsize(file_path)
                        extension = os.path.splitext(file)[1].lower()
                        
                        stats['total_files'] += 1
                        stats['total_size'] += file_size
                        
                        # Count extensions
                        stats['extensions'][extension] = stats['extensions'].get(extension, 0) + 1
                        
                        # Check if it's a text file
                        if extension in self.text_extensions or self._is_text_file(file_path):
                            stats['text_files'] += 1
                        
                        # Track largest file
                        if file_size > stats['largest_file']['size']:
                            stats['largest_file'] = {'name': file, 'size': file_size}
                        
                        # Track smallest file
                        if file_size < stats['smallest_file']['size']:
                            stats['smallest_file'] = {'name': file, 'size': file_size}
                            
                    except Exception as e:
                        self.logger.warning(f"Could not stat file {file_path}: {str(e)}")
            
            # Clean up smallest file if no files found
            if stats['smallest_file']['size'] == float('inf'):
                stats['smallest_file'] = {'name': '', 'size': 0}
            
            self.logger.debug(f"Directory stats for {directory}: {stats}")
            
        except Exception as e:
            self.logger.error(f"Error getting directory stats for {directory}: {str(e)}")
        
        return stats

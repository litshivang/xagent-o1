"""
Configuration settings for AI Travel Agent
"""

import os
from pathlib import Path

class Config:
    """Configuration class for the AI Travel Agent application"""
    
    # Project directories
    PROJECT_ROOT = Path(__file__).parent
    INQUIRIES_DIR = PROJECT_ROOT / "inquiries"
    OUTPUT_DIR = PROJECT_ROOT / "output"
    LOGS_DIR = PROJECT_ROOT / "logs"
    TEMPLATES_DIR = PROJECT_ROOT / "templates"
    
    # File settings
    DEFAULT_OUTPUT_FILE = OUTPUT_DIR / "travel_inquiries_report.xlsx"
    LOG_FILE = LOGS_DIR / "travel_agent.log"
    
    # Processing settings
    MAX_WORKERS = min(32, (os.cpu_count() or 1) + 4)  # Optimal for I/O bound tasks
    TASK_TIMEOUT = 30  # seconds per task
    BATCH_SIZE = 100  # files per batch
    
    # Text processing settings
    MIN_TEXT_LENGTH = 10  # minimum characters for valid inquiry
    MAX_TEXT_LENGTH = 10000  # maximum characters to process
    
    # ML Model settings
    NER_MODEL_NAME = "dbmdz/bert-large-cased-finetuned-conll03-english"
    NER_CONFIDENCE_THRESHOLD = 0.5
    SPACY_MODEL = "en_core_web_sm"  # Default spaCy model
    
    # Entity extraction settings
    ENTITY_TYPES = {
        'PERSON': 'customer_name',
        'DATE': 'travel_dates',
        'GPE': 'destination',  # Geopolitical entity
        'LOC': 'destination',  # Location
        'MONEY': 'budget',
        'CARDINAL': 'travelers_count',
        'EMAIL': 'contact_info',
        'PHONE': 'contact_info'
    }
    
    # Excel template settings
    EXCEL_COLUMNS = [
        'File Name',
        'Customer Name',
        'Travel Dates',
        'Destination',
        'Budget',
        'Number of Travelers',
        'Contact Information',
        'Special Requirements',
        'Processing Status',
        'Processing Time (seconds)',
        'Extraction Method'
    ]
    
    # Regex patterns for rule-based extraction
    REGEX_PATTERNS = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'(?:\+91[-\s]?)?[6-9]\d{9}',
        'currency_inr': r'(?:Rs\.?|INR|₹)\s*[\d,]+(?:\.\d{2})?',
        'currency_usd': r'(?:\$|USD)\s*[\d,]+(?:\.\d{2})?',
        'date_patterns': [
            r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b',
            r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:st|nd|rd|th)?\b'
        ],
        'traveler_count': r'\b(\d+)\s*(?:people|persons?|travelers?|pax|adults?)\b',
        'duration': r'\b(\d+)\s*(?:days?|nights?|weeks?)\b'
    }
    
    # Indian cities and destinations (common ones)
    INDIAN_DESTINATIONS = {
        'goa', 'kerala', 'rajasthan', 'himachal', 'kashmir', 'delhi', 'mumbai',
        'bangalore', 'hyderabad', 'chennai', 'kolkata', 'pune', 'ahmedabad',
        'jaipur', 'udaipur', 'jodhpur', 'manali', 'shimla', 'darjeeling',
        'ooty', 'kodaikanal', 'munnar', 'alleppey', 'kochi', 'trivandrum',
        'pondicherry', 'mahabalipuram', 'hampi', 'mysore', 'coorg', 'agra',
        'varanasi', 'rishikesh', 'haridwar', 'amritsar', 'chandigarh'
    }
    
    # Logging configuration
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Performance thresholds
    TARGET_PROCESSING_TIME = 60  # seconds for 100 files
    WARNING_THRESHOLD = 0.8  # 80% of target time
    
    @classmethod
    def get_env_var(cls, var_name: str, default_value: str = "") -> str:
        """Get environment variable with fallback"""
        return os.getenv(var_name, default_value)

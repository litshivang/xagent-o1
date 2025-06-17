"""
Modules package for AI Travel Agent
Contains all the core processing modules
"""

__version__ = "1.0.0"
__author__ = "AI Travel Agent Team"

# Import main classes for easy access
from .text_preprocessor import TextPreprocessor
from .ml_extractor import MLExtractor
from .rule_extractor import RuleExtractor
from .fusion_engine import FusionEngine
from .excel_generator import ExcelGenerator

__all__ = [
    'TextPreprocessor',
    'MLExtractor', 
    'RuleExtractor',
    'FusionEngine',
    'ExcelGenerator'
]

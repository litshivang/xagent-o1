"""
Setup script for AI Travel Agent
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    """Read README.md file"""
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return "AI Travel Agent - Process customer inquiries using hybrid ML/rule-based extraction"

# Read requirements
def read_requirements():
    """Read requirements.txt file"""
    try:
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except:
        return []

setup(
    name="ai-travel-agent",
    version="1.0.0",
    description="AI Travel Agent - Process customer inquiries using hybrid ML/rule-based extraction",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="AI Travel Agent Team",
    author_email="team@ai-travel-agent.com",
    url="https://github.com/ai-travel-agent/ai-travel-agent",
    packages=find_packages(),
    include_package_data=True,
    install_requires=read_requirements(),
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'pytest-cov>=4.1.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.6.0'
        ],
        'gpu': [
            'torch>=2.0.0+cu118',  # CUDA support
        ]
    },
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Text Processing :: Linguistic',
        'Topic :: Office/Business :: Financial :: Spreadsheet',
    ],
    keywords='ai, nlp, travel, agent, extraction, excel, bert, spacy',
    entry_points={
        'console_scripts': [
            'ai-travel-agent=main:main',
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/ai-travel-agent/ai-travel-agent/issues',
        'Source': 'https://github.com/ai-travel-agent/ai-travel-agent',
        'Documentation': 'https://ai-travel-agent.readthedocs.io/',
    },
)

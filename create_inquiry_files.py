"""
Create Individual Inquiry Files from Bulk Data
"""

import os
from pathlib import Path

def process_bulk_file(file_path, language_prefix):
    """Process bulk file and create individual inquiry files"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by email separators
    emails = content.split('---')
    
    created_files = []
    for i, email in enumerate(emails, 1):
        email = email.strip()
        if email and len(email) > 50:  # Valid email content
            file_name = f"{language_prefix}_{i:03d}.txt"
            file_path = f"inquiries/{file_name}"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(email)
            
            created_files.append(file_name)
    
    return created_files

def main():
    """Process all bulk data files"""
    Path("inquiries").mkdir(exist_ok=True)
    
    # Define bulk files
    bulk_files = [
        ('attached_assets/english_emails_1749953080878.txt', 'english'),
        ('attached_assets/hindi_emails_1749953080877.txt', 'hindi'),
        ('attached_assets/hindi_english_emails_1749953080879.txt', 'hindi_eng'),
        ('attached_assets/hinglish_mix_emails_1749953080879.txt', 'hinglish')
    ]
    
    total_files = 0
    for file_path, prefix in bulk_files:
        if os.path.exists(file_path):
            created = process_bulk_file(file_path, prefix)
            print(f"Created {len(created)} files for {prefix}")
            total_files += len(created)
        else:
            print(f"File not found: {file_path}")
    
    print(f"Total inquiry files created: {total_files}")

if __name__ == "__main__":
    main()
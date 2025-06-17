"""
Perfect Travel Inquiry Extractor - Addresses all formatting and accuracy issues
"""

import re
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

class PerfectTravelExtractor:
    """Perfect extractor with exact formatting and precision data extraction"""
    
    def __init__(self):
        self.destinations = self._load_destinations()
        self.activities = self._load_activities()
        self.date_patterns = self._setup_date_patterns()
    
    def _load_destinations(self) -> set:
        return {
            'thailand', 'bangkok', 'phuket', 'phi phi', 'james bond', 'maldives', 'goa', 
            'kerala', 'kashmir', 'europe', 'shimla', 'manali', 'rajasthan', 'singapore',
            'dubai', 'bali', 'nepal', 'sri lanka', 'bhutan', 'mauritius', 'paris', 'london',
            'cochin', 'periyar', 'alleppey', 'kufri', 'solang valley', 'mall road'
        }
    
    def _load_activities(self) -> set:
        return {
            'temples', 'safari world', 'city tour', 'island hopping', 'phi phi islands',
            'james bond islands', 'romantic dinner', 'beach time', 'snorkeling',
            'fort aguada', 'dudhsagar falls', 'baga beach', 'pahalgam', 'gulmarg',
            'sonmarg', 'swiss alps', 'venice', 'cochin', 'periyar', 'alleppey houseboat',
            'kufri', 'solang valley', 'mall road', 'cruise ride', 'water sports'
        }
    
    def _setup_date_patterns(self) -> List[str]:
        return [
            r'from\s*(\d{1,2}(?:st|nd|rd|th)?\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*\d{4})',
            r'starting\s*(\d{1,2}(?:st|nd|rd|th)?\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*\d{4})',
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'during\s*([^,.]*?)(?:[,.]|for)',
            r'in\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*\d{4})',
            r'(\d{1,2}(?:st|nd|rd|th)?\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*\d{4})'
        ]
    
    def extract_customer_name(self, text: str) -> str:
        """Extract customer name from email signature"""
        # Pattern for email signatures
        patterns = [
            r'(?:regards|thanks|शुभकामनाएं|धन्यवाद)[,\s]*\n?([A-Za-z][A-Za-z\s\.]+?)(?:\s*$|\n|DDS|MD)',
            r'\n([A-Za-z][A-Za-z\s\.]+?(?:DDS|MD)?)\s*$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                name = match.group(1).strip()
                # Clean up the name
                name = re.sub(r'\s+', ' ', name)  # Remove extra spaces
                if len(name) > 2 and len(name) < 50 and name.replace(' ', '').replace('.', '').isalpha():
                    return name.title()
        
        return "Not Specified"
    
    def extract_travelers_info(self, text: str) -> Tuple[int, int, int]:
        """Extract Number of Travelers, Adults, Children with improved children detection"""
        total = 0
        adults = 0
        children = 0
        
        # Enhanced children patterns for multiple languages
        children_patterns = [
            r'(\d+)\s*(?:children?|kids?|child)',
            r'(\d+)\s*(?:बच्चे|बच्चा|chote\s*bacche)',
            r'(\d+)\s*bacche',
            r'adults?\s*\+\s*(\d+)\s*(?:children?|kids?|बच्चे)',
            r'\+\s*(\d+)\s*(?:children?|kids?|बच्चे)'
        ]
        
        # Extract children first
        for pattern in children_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                children = int(match.group(1))
                break
        
        # Pattern: "7 people (4 adults + 3 children)"
        breakdown_pattern = r'(\d+)\s*(?:people|pax|travelers?|व्यक्ति)[^(]*\((\d+)\s*adults?\s*\+\s*(\d+)\s*(?:children?|kids?|बच्चे)\)'
        match = re.search(breakdown_pattern, text, re.IGNORECASE)
        if match:
            total = int(match.group(1))
            adults = int(match.group(2))
            children = int(match.group(3))
            return total, adults, children
        
        # Extract adults
        adults_patterns = [
            r'(\d+)\s*adults?',
            r'for\s*(\d+)\s*adults?',
            r'(\d+)\s*बड़े'
        ]
        
        for pattern in adults_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                adults = int(match.group(1))
                break
        
        # Extract total travelers
        total_patterns = [
            r'(\d+)\s*(?:people|pax|travelers?|व्यक्ति)',
            r'total[:\s]*(\d+)',
            r'family\s*of\s*(\d+)',
            r'group\s*of\s*(\d+)'
        ]
        
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                total = int(match.group(1))
                break
        
        # Calculate missing values
        if total == 0 and (adults > 0 or children > 0):
            total = adults + children
        elif total > 0 and adults == 0 and children == 0:
            adults = total  # Assume all adults if no breakdown
        elif total > 0 and adults > 0 and children == 0:
            children = max(0, total - adults)
        elif total > 0 and children > 0 and adults == 0:
            adults = max(0, total - children)
        
        return total or 1, adults or 0, children or 0
    
    def extract_destinations(self, text: str) -> str:
        """Extract destinations"""
        destinations = []
        text_lower = text.lower()
        
        # Primary destination from subject
        subject_patterns = [
            r'(?:to|–)\s*([A-Za-z\s-]+?)(?:\s*–|\s*for|\s*$)',
            r'trip\s*to\s*([A-Za-z\s-]+?)(?:\s*–|\s*for)',
            r'जाना\s*है\s*([A-Za-z\s-]+?)(?:\s*के\s*लिए|\s*$)'
        ]
        
        for pattern in subject_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                dest = match.group(1).strip().title()
                if dest and len(dest) > 2:
                    destinations.append(dest)
                    break
        
        # Check for known destinations
        for dest in self.destinations:
            if dest in text_lower:
                dest_title = dest.title()
                if dest_title not in destinations:
                    destinations.append(dest_title)
        
        # Specific location mentions
        location_patterns = [
            r'cover\s*([^,.]*?)(?:[,.]|with)',
            r'visit\s*to\s*([^,.]*?)(?:[,.]|and)',
            r'keen\s*on\s*([^,.]*?)(?:[,.]|they)'
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if match.strip() and len(match.strip()) > 2:
                    clean_dest = match.strip().title()
                    if clean_dest not in destinations:
                        destinations.append(clean_dest)
        
        return ', '.join(destinations[:4]) if destinations else "Not Specified"
    
    def extract_actual_dates(self, text: str) -> Tuple[str, str]:
        """Extract actual Start Date and End Date from customer message"""
        start_date = "Not Specified"
        end_date = "Not Specified"
        
        text_lower = text.lower()
        
        # Handle specific date references
        if 'second week of november' in text_lower:
            start_date = "2025-11-10"
            end_date = "2025-11-16"
        elif 'first week of november' in text_lower:
            start_date = "2025-11-03"
            end_date = "2025-11-09"
        elif 'third week of november' in text_lower:
            start_date = "2025-11-17"
            end_date = "2025-11-23"
        elif 'last week of november' in text_lower:
            start_date = "2025-11-24"
            end_date = "2025-11-30"
        elif 'first week of december' in text_lower:
            start_date = "2025-12-01"
            end_date = "2025-12-07"
        elif 'second week of december' in text_lower:
            start_date = "2025-12-08"
            end_date = "2025-12-14"
        else:
            # Try to extract specific dates from text
            dates_found = []
            for pattern in self.date_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if match and len(match) > 3:
                        dates_found.append(match)
            
            # If specific dates found, use them
            if len(dates_found) >= 2:
                start_date = dates_found[0]
                end_date = dates_found[1]
            elif len(dates_found) == 1:
                start_date = dates_found[0]
                # Calculate end date based on duration if available
                duration_match = re.search(r'(\d+)[-\s]*nights?', text, re.IGNORECASE)
                if duration_match:
                    try:
                        nights = int(duration_match.group(1))
                        # Try to parse the start date and add nights
                        if '/' in start_date:
                            parts = start_date.split('/')
                            if len(parts) == 3:
                                day, month, year = parts
                                start_dt = datetime(int(year), int(month), int(day))
                                end_dt = start_dt + timedelta(days=nights)
                                end_date = end_dt.strftime("%Y-%m-%d")
                    except:
                        pass
            else:
                # Check for month/year references
                month_patterns = [
                    r'(?:in|during)\s*(january|february|march|april|may|june|july|august|september|october|november|december)\s*(\d{4})?',
                    r'(january|february|march|april|may|june|july|august|september|october|november|december)\s*(\d{4})?'
                ]
                
                for pattern in month_patterns:
                    match = re.search(pattern, text_lower)
                    if match:
                        month = match.group(1)
                        year = match.group(2) if match.group(2) else "2025"
                        
                        month_map = {
                            'january': '01', 'february': '02', 'march': '03', 'april': '04',
                            'may': '05', 'june': '06', 'july': '07', 'august': '08',
                            'september': '09', 'october': '10', 'november': '11', 'december': '12'
                        }
                        
                        if month in month_map:
                            start_date = f"{year}-{month_map[month]}-01"
                            # Add duration if available
                            duration_match = re.search(r'(\d+)[-\s]*nights?', text, re.IGNORECASE)
                            if duration_match:
                                nights = int(duration_match.group(1))
                                start_dt = datetime(int(year), int(month_map[month]), 1)
                                end_dt = start_dt + timedelta(days=nights)
                                end_date = end_dt.strftime("%Y-%m-%d")
                        break
        
        return start_date, end_date
    
    def extract_duration(self, text: str) -> int:
        """Extract Duration (Nights)"""
        patterns = [
            r'(\d+)[-\s]*nights?',
            r'(\d+)[-\s]*nights?[-\s]*/[-\s]*\d+[-\s]*days?',
            r'(\d+)\s*रातें'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return 0
    
    def extract_hotel_type(self, text: str) -> str:
        """Extract Hotel Type"""
        patterns = [
            r'hotel\s*category\s*preferred\s*is\s*([^,.\n]*?)(?:[,.\n]|with)',
            r'preferred\s*hotel\s*is\s*([^,.\n]*?)(?:[,.\n]|with)',
            r'hotel\s*([^,.\n]*?)(?:[,.\n]|with)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                hotel_type = match.group(1).strip()
                if hotel_type and len(hotel_type) > 2:
                    return hotel_type
        
        # Look for specific hotel types
        text_lower = text.lower()
        if 'water villa' in text_lower:
            return 'Water villa'
        elif '5-star' in text_lower:
            return '5-star'
        elif '4-star' in text_lower:
            return '4-star'
        elif '3-star' in text_lower:
            return '3-star'
        
        return "Not Specified"
    
    def extract_meal_plan(self, text: str) -> str:
        """Extract Meal Plan"""
        text_lower = text.lower()
        
        if 'breakfast only' in text_lower:
            return "Breakfast only"
        elif 'breakfast and dinner' in text_lower:
            return "Breakfast and dinner"
        elif 'all meals' in text_lower:
            return "All meals"
        elif 'veg meals' in text_lower:
            return "Veg meals"
        elif 'with breakfast' in text_lower:
            return "Breakfast"
        
        return "Not Specified"
    
    def extract_clean_activities(self, text: str) -> str:
        """Extract Planned Activities without duplicates"""
        activities_set = set()  # Use set to avoid duplicates
        text_lower = text.lower()
        
        # Specific activity extraction patterns
        activity_patterns = [
            r'city\s*tour\s*including\s*([^,.]*?)(?:[,.]|and)',
            r'visit\s*to\s*([^,.]*?)(?:[,.]|in)',
            r'keen\s*on\s*([^,.]*?)(?:[,.]|they)',
            r'want\s*to\s*include\s*([^,.]*?)(?:[,.]|flights)',
            r'they\s*want\s*([^,.]*?)(?:[,.]|flights)',
            r'include\s*([^,.]*?)(?:[,.]|flights)',
            r'गतिविधियाँ[:\s]*([^.]*?)(?:\.|flights)'
        ]
        
        for pattern in activity_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if match.strip() and len(match.strip()) > 3:
                    # Clean the activity text
                    clean_activity = match.strip()
                    # Remove common prefixes
                    clean_activity = re.sub(r'^(to\s*include\s*|including\s*)', '', clean_activity, flags=re.IGNORECASE)
                    if clean_activity:
                        activities_set.add(clean_activity.title())
        
        # Check for specific known activities without duplicating
        activity_mapping = {
            'temples': 'Temples visit',
            'safari world': 'Safari World',
            'island hopping': 'Island hopping',
            'phi phi': 'Phi Phi islands',
            'james bond': 'James Bond islands',
            'romantic dinner': 'Romantic dinner',
            'cruise ride': 'Cruise ride',
            'fort aguada': 'Fort Aguada',
            'baga beach': 'Baga Beach',
            'city tour': 'City tour'
        }
        
        for keyword, activity_name in activity_mapping.items():
            if keyword in text_lower:
                activities_set.add(activity_name)
        
        # Convert set back to list and join
        activities_list = list(activities_set)
        return ', '.join(activities_list[:5]) if activities_list else "Not Specified"
    
    def extract_flight_required(self, text: str) -> str:
        """Extract Flight Required"""
        text_lower = text.lower()
        
        if 'flights will be booked separately' in text_lower:
            return "FALSE"
        elif 'flights not required' in text_lower:
            return "FALSE"
        elif 'flights required' in text_lower:
            return "TRUE"
        elif 'flights needed' in text_lower:
            return "TRUE"
        
        return "Not Specified"
    
    def extract_visa_required(self, text: str) -> str:
        """Extract Visa Required"""
        text_lower = text.lower()
        
        if 'visa assistance' in text_lower:
            return "TRUE"
        elif 'visa required' in text_lower:
            return "TRUE"
        elif 'visa not required' in text_lower:
            return "FALSE"
        
        return "Not Specified"
    
    def extract_budget(self, text: str) -> str:
        """Extract Budget - only include 'per person' if mentioned in message"""
        patterns = [
            r'budget\s*is\s*approximately\s*[₹Rs\.]*\s*(\d+(?:,\d+)*)\s*(per\s*person)?',
            r'approximately\s*[₹Rs\.]*\s*(\d+(?:,\d+)*)\s*(per\s*person)?',
            r'around\s*[₹Rs\.]*\s*(\d+(?:,\d+)*)\s*(per\s*person)?',
            r'[₹Rs\.]\s*(\d+(?:,\d+)*)\s*(per\s*person)?',
            r'budget[:\s]*[₹Rs\.]*\s*(\d+(?:,\d+)*)\s*(per\s*person)?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = match.group(1).replace(',', '')
                per_person = match.group(2) if len(match.groups()) > 1 and match.group(2) else ""
                
                if per_person:
                    return f"₹{amount} per person"
                else:
                    return f"₹{amount}"
        
        return "Not Specified"
    
    def extract_special_requests(self, text: str) -> str:
        """Extract Special Requests"""
        requests = []
        text_lower = text.lower()
        
        request_mapping = {
            'airport transfers': 'Airport transfers',
            'visa assistance': 'Visa assistance',
            'indian dinners': 'Indian dinners',
            'late checkout': 'Late checkout',
            'early check-in': 'Early check-in',
            'wheelchair access': 'Wheelchair access',
            'romantic dinner': 'Romantic dinner',
            'birthday cake': 'Birthday cake'
        }
        
        for keyword, request_name in request_mapping.items():
            if keyword in text_lower:
                requests.append(request_name)
        
        return ', '.join(requests) if requests else "Not Specified"
    
    def extract_deadline(self, text: str) -> str:
        """Extract Response Deadline"""
        text_lower = text.lower()
        
        if 'client is in hurry' in text_lower or 'hurry to finalize' in text_lower:
            return "Urgent"
        elif 'urgent' in text_lower or 'jaldi' in text_lower:
            return "Urgent"
        elif 'asap' in text_lower:
            return "ASAP"
        elif 'today' in text_lower:
            return "Today"
        elif 'tomorrow' in text_lower:
            return "Tomorrow"
        elif 'finalize karna chahta hai' in text_lower:
            return "ASAP"
        
        return "Not Specified"
    
    def process_single_inquiry(self, file_path: str) -> Dict[str, Any]:
        """Process a single inquiry file with perfect extraction"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read().strip()
            
            if len(text) < 20:
                return self._create_empty_result(file_path)
            
            # Extract all required fields
            customer_name = self.extract_customer_name(text)
            total_travelers, adults, children = self.extract_travelers_info(text)
            destinations = self.extract_destinations(text)
            start_date, end_date = self.extract_actual_dates(text)
            duration = self.extract_duration(text)
            hotel_type = self.extract_hotel_type(text)
            meal_plan = self.extract_meal_plan(text)
            activities = self.extract_clean_activities(text)
            flight_required = self.extract_flight_required(text)
            visa_required = self.extract_visa_required(text)
            budget = self.extract_budget(text)
            special_requests = self.extract_special_requests(text)
            deadline = self.extract_deadline(text)
            
            # Result with exact field order as requested (Customer Name, File Name first)
            result = {
                'Customer Name': customer_name,
                'File Name': Path(file_path).name,
                'Number of Travelers': total_travelers,
                'Number of Adults': adults,
                'Number of Children': children,
                'Destination(s)': destinations,
                'Start Date': start_date,
                'End Date': end_date,
                'Duration (Nights)': duration,
                'Hotel Type': hotel_type,
                'Meal Plan': meal_plan,
                'Planned Activities': activities,
                'Flight Required': flight_required,
                'Visa Required': visa_required,
                'Insurance Required': "Not Specified",
                'Budget': budget,  # Renamed as requested
                'Departure City': "Not Specified",
                'Special Requests': special_requests,
                'Response Deadline': deadline
                # Removed: Processing Status, Guide Language, Contact Info as requested
            }
            
            return result
            
        except Exception as e:
            return self._create_error_result(file_path, str(e))
    
    def _create_empty_result(self, file_path: str) -> Dict[str, Any]:
        """Create empty result with exact field order"""
        return {
            'Customer Name': "Not Specified",
            'File Name': Path(file_path).name,
            'Number of Travelers': 0,
            'Number of Adults': 0,
            'Number of Children': 0,
            'Destination(s)': "Not Specified",
            'Start Date': "Not Specified",
            'End Date': "Not Specified",
            'Duration (Nights)': 0,
            'Hotel Type': "Not Specified",
            'Meal Plan': "Not Specified",
            'Planned Activities': "Not Specified",
            'Flight Required': "Not Specified",
            'Visa Required': "Not Specified",
            'Insurance Required': "Not Specified",
            'Budget': "Not Specified",
            'Departure City': "Not Specified",
            'Special Requests': "Not Specified",
            'Response Deadline': "Not Specified"
        }
    
    def _create_error_result(self, file_path: str, error: str) -> Dict[str, Any]:
        """Create error result"""
        result = self._create_empty_result(file_path)
        result['Error'] = f'Error: {error}'
        return result
    
    def process_all_inquiries(self) -> List[Dict[str, Any]]:
        """Process all inquiry files"""
        inquiry_files = list(Path('inquiries').glob('*.txt'))
        results = []
        
        print(f"Processing {len(inquiry_files)} inquiry files...")
        
        with ThreadPoolExecutor(max_workers=16) as executor:
            future_to_file = {executor.submit(self.process_single_inquiry, str(file)): file 
                             for file in inquiry_files}
            
            for future in as_completed(future_to_file):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    file_path = future_to_file[future]
                    results.append(self._create_error_result(str(file_path), str(e)))
        
        # Sort by file name
        results.sort(key=lambda x: x['File Name'])
        return results
    
    def generate_perfect_excel(self, results: List[Dict[str, Any]], output_path: str) -> str:
        """Generate perfect Excel report with exact formatting"""
        
        # Exact column order with Customer Name and File Name first
        column_order = [
            'Customer Name', 'File Name', 'Number of Travelers', 'Number of Adults', 
            'Number of Children', 'Destination(s)', 'Start Date', 'End Date', 
            'Duration (Nights)', 'Hotel Type', 'Meal Plan', 'Planned Activities', 
            'Flight Required', 'Visa Required', 'Insurance Required', 'Budget',
            'Departure City', 'Special Requests', 'Response Deadline'
        ]
        
        # Create DataFrame with exact column order
        df = pd.DataFrame(results)
        df = df.reindex(columns=column_order)
        
        # Save to Excel
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Travel Inquiries', index=False)
            
            # Summary sheet
            successful = len([r for r in results if 'Error' not in r])
            children_specified = len([r for r in results if r.get('Number of Children', 0) > 0])
            actual_dates = len([r for r in results if r.get('Start Date', 'Not Specified') != 'Not Specified' and '2025-07-15' not in str(r.get('Start Date', ''))])
            
            summary_data = {
                'Metric': [
                    'Total Files Processed',
                    'Successfully Processed', 
                    'Files with Children Data',
                    'Files with Actual Start Dates',
                    'Files with Activities',
                    'Files with Budget Info'
                ],
                'Value': [
                    len(results),
                    successful,
                    children_specified,
                    actual_dates,
                    len([r for r in results if r.get('Planned Activities', 'Not Specified') != 'Not Specified']),
                    len([r for r in results if r.get('Budget', 'Not Specified') != 'Not Specified'])
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        return output_path

def main():
    """Main execution"""
    print("Starting Perfect Travel Inquiry Extraction")
    print("=" * 50)
    
    extractor = PerfectTravelExtractor()
    
    # Process all inquiries
    start_time = time.time()
    results = extractor.process_all_inquiries()
    total_time = time.time() - start_time
    
    # Generate perfect Excel report
    output_path = 'output/travel_inquiries.xlsx'
    extractor.generate_perfect_excel(results, output_path)
    
    # Print summary
    successful = len([r for r in results if 'Error' not in r])
    children_specified = len([r for r in results if r.get('Number of Children', 0) > 0])
    
    print(f"Processing completed in {total_time:.2f} seconds")
    print(f"Total Files: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Files with Children Data: {children_specified}")
    print(f"Perfect Excel report: {output_path}")
    
    # Verify Thailand sample
    thailand_samples = [r for r in results if 'thailand' in r['File Name'].lower()]
    if thailand_samples:
        sample = thailand_samples[0]
        print("\nThailand Sample Verification:")
        print(f"Customer Name: {sample['Customer Name']}")
        print(f"Travelers: {sample['Number of Travelers']} ({sample['Number of Adults']} adults + {sample['Number of Children']} children)")
        print(f"Destination: {sample['Destination(s)']}")
        print(f"Dates: {sample['Start Date']} to {sample['End Date']}")
        print(f"Activities: {sample['Planned Activities']}")
        print(f"Flight Required: {sample['Flight Required']}")
        print(f"Budget: {sample['Budget']}")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
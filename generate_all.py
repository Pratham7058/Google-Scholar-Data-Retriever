from scholarly import scholarly
import pandas as pd
from datetime import datetime
import time
import random
import re

def extract_issn(bib_text):
    """
    Extract ISSN number from bibliography text
    ISSN format: four digits, hyphen, four digits (e.g., 1234-5678)
    Can be preceded by 'ISSN' or just be the number
    """
    patterns = [
        r'ISSN:?\s*(\d{4}-\d{4})',  # matches "ISSN 1234-5678" or "ISSN: 1234-5678"
        r'[\s\(](\d{4}-\d{4})[\s\)]',  # matches " 1234-5678 " or "(1234-5678)"
        r'eISSN:?\s*(\d{4}-\d{4})',  # matches electronic ISSN
        r'pISSN:?\s*(\d{4}-\d{4})'   # matches print ISSN
    ]
    
    for pattern in patterns:
        match = re.search(pattern, str(bib_text))
        if match:
            return match.group(1)
    return ''

def extract_isbn(bib_text):
    """
    Extract ISBN number from bibliography text
    Handles both ISBN-10 (10 digits) and ISBN-13 (13 digits) formats
    Can include hyphens or spaces
    """
    patterns = [
        r'ISBN-13:?\s*([\d-]{17})',  # matches "ISBN-13: 978-0-123-45678-9"
        r'ISBN-10:?\s*([\d-]{13})',  # matches "ISBN-10: 0-123-45678-9"
        r'ISBN:?\s*([\d-]{13,17})',  # matches "ISBN: ..." for either format
        r'[\s\(](978[\d-]{10,14})[\s\)]',  # matches ISBN-13 without prefix
        r'[\s\(]([\d-]{10,13})[\s\)]'  # matches ISBN-10 without prefix
    ]
    
    for pattern in patterns:
        match = re.search(pattern, str(bib_text))
        if match:
            # Remove hyphens and spaces from the matched ISBN
            isbn = re.sub(r'[-\s]', '', match.group(1))
            if len(isbn) in [10, 13]:  # Validate length
                return isbn
    return ''

def extract_page_numbers(bib_text):
    """
    Extract page numbers from bibliography text with enhanced pattern matching
    Returns tuple of (start_page, end_page, page_count)
    """
    patterns = [
        # Standard page ranges
        r'pp?\.?\s*(\d+)\s*[-–—]\s*(\d+)',  # matches "pp. 123-456" or "p. 123-456"
        r'pages?\s*(\d+)\s*[-–—]\s*(\d+)',  # matches "pages 123-456" or "page 123-456"
        r'[\s\(](\d+)\s*[-–—]\s*(\d+)[\s\)]',  # matches " 123-456 " or "(123-456)"
        
        # Article number with page range
        r'Article\s+\d+,?\s+pp?\.?\s*(\d+)\s*[-–—]\s*(\d+)',  # matches "Article 7, pp. 123-456"
        
        # Pages with various separators
        r'(\d+)\s*[-–—:]\s*(\d+)',  # matches different types of dashes and colons
        
        # Single page number
        r'pp?\.?\s*(\d+)(?!\d)',  # matches "p. 123" or "pp. 123"
        r'pages?\s*(\d+)(?!\d)',  # matches "page 123" or "pages 123"
        
        # Page numbers with volume/issue
        r'Vol\.\s*\d+\s*[,:]\s*(?:No\.\s*\d+\s*[,:]\s*)?pp?\.?\s*(\d+)\s*[-–—]\s*(\d+)',
        
        # Elsevier-style page numbers
        r'[Pp]ages?\s*(\d+)[Ee]\d+\s*[-–—]\s*(\d+)[Ee]\d+',
    ]
    
    # First try to find patterns with page ranges
    for pattern in patterns[:-2]:  # Exclude single page patterns initially
        match = re.search(pattern, str(bib_text))
        if match:
            try:
                start_page = match.group(1)
                end_page = match.group(2)
                # Remove any leading zeros
                start_page = str(int(start_page))
                end_page = str(int(end_page))
                # Calculate page count
                page_count = int(end_page) - int(start_page) + 1
                return start_page, end_page, str(page_count)
            except (ValueError, IndexError):
                continue
    
    # If no range found, try to find single page number
    for pattern in patterns[-2:]:  # Only single page patterns
        match = re.search(pattern, str(bib_text))
        if match:
            try:
                page = str(int(match.group(1)))  # Remove leading zeros
                return page, page, '1'  # Single page, so start = end, count = 1
            except (ValueError, IndexError):
                continue
    
    # Try to find any sequence of digits that might be a page number
    # but only if it's reasonable (not too large, not a year)
    numbers = re.findall(r'(\d+)', str(bib_text))
    for num in numbers:
        try:
            page_num = int(num)
            # Exclude likely years and unreasonably large numbers
            if 1 <= page_num <= 9999 and not (1900 <= page_num <= 2100):
                return str(page_num), str(page_num), '1'
        except ValueError:
            continue
    
    return '', '', ''

def extract_issue(bib_text):
    """
    Extract issue number from bibliography text
    """
    patterns = [
        r'issue\s*(\d+)',        # matches "issue 123"
        r'no\.\s*(\d+)',         # matches "no. 123"
        r'\((\d+)\)',            # matches "(123)"
        r'#(\d+)',               # matches "#123"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, str(bib_text).lower())
        if match:
            return match.group(1)
    
    return ''

def extract_conference_name(venue, title):
    """
    Extract conference name from venue and title
    """
    conf_indicators = ['conference', 'conf', 'symposium', 'workshop', 'proceedings']
    
    if venue:
        return venue
    
    # Fixed escape sequence by using raw string
    for indicator in conf_indicators:
        match = re.search(r".*?(" + re.escape(indicator) + r".*?)(20\d{2}|19\d{2}|[\.,]|$)", 
                         str(title), 
                         re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return ''

def scrape_scholar_data(search_query, max_retries=3):
    """
    Scrape all publication data from Google Scholar without using a proxy
    """
    publications_data = []
    
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1} of {max_retries}")
            search_query_result = scholarly.search_author(search_query)
            
            try:
                author = next(search_query_result)
                author = scholarly.fill(author)
            except StopIteration:
                print("No author found with that name")
                return publications_data
            
            for i, pub in enumerate(author['publications'], 1):
                try:
                    filled_pub = scholarly.fill(pub)
                    bib = filled_pub.get('bib', {})
                    
                    # Combine all possible sources of page information
                    full_text = (
                        str(bib.get('citation', '')) + 
                        str(bib.get('abstract', '')) + 
                        str(bib.get('note', '')) +
                        str(bib.get('volume', '')) +
                        str(bib.get('pages', ''))
                    )
                    
                    # Extract page numbers
                    start_page, end_page, page_count = extract_page_numbers(full_text)
                    
                    # Extract issue number
                    issue = extract_issue(
                        str(bib.get('citation', '')) + str(bib.get('volume', ''))
                    )
                    
                    # Extract conference name
                    conference_name = extract_conference_name(
                        bib.get('venue', ''),
                        bib.get('title', '')
                    )
                    
                    # Extract ISSN and ISBN
                    issn = extract_issn(full_text)
                    isbn = extract_isbn(full_text)
                    
                    publication = {
                        'Author Name': search_query,
                        'Title': bib.get('title', ''),
                        'Academic year': bib.get('pub_year', ''),
                        'Year': bib.get('pub_year', ''),
                        'Name of Conference': conference_name,
                        'Name of Journal': bib.get('journal', ''),
                        'Volume': bib.get('volume', ''),
                        'Issue': issue,
                        'Page start': start_page,
                        'Page end': end_page,
                        'Page count': page_count,
                        'Cited by': filled_pub.get('num_citations', ''),
                        'DOI': filled_pub.get('pub_url', ''),
                        'Date': bib.get('pub_year', ''),
                        'h index': author.get('hindex', ''),
                        'i index': author.get('i10index', ''),
                        'Publisher': bib.get('publisher', ''),
                        'ISSN': issn,
                        'ISBN': isbn
                    }
                    
                    publications_data.append(publication)
                    print(f"Processed publication: {bib.get('title', '')}")
                    time.sleep(random.uniform(2, 5))  # Add random sleep to prevent getting blocked
                    
                except Exception as e:
                    print(f"Error processing publication: {str(e)}")
                    continue
            
            break
            
        except Exception as e:
            print(f"Error during attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                print(f"Waiting {wait_time} seconds before retrying...")
                time.sleep(wait_time)
            else:
                print("Max retries reached. Please try again later.")
    
    return publications_data

def generate_excel_file(search_query, max_retries=3):
    """
    Generates an Excel file with the scraped publication data
    """
    publications_data = scrape_scholar_data(search_query, max_retries)
    
    if publications_data:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scholar_data_{timestamp}.xlsx"
        save_to_excel(publications_data, filename)
        return filename
    else:
        return None

def save_to_excel(data, filename):
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    print(f"Data saved to {filename}")
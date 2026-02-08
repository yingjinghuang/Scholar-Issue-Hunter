#!/usr/bin/env python3
"""
Academic Journal Special Issues Scraper
Scrapes special issue information from academic journals
"""

import json
import os
from datetime import datetime
from typing import List, Dict
import requests
from bs4 import BeautifulSoup
import time

class JournalScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.journals = [
            {
                'name': 'Remote Sensing of Environment',
                'url': 'https://www.sciencedirect.com/journal/remote-sensing-of-environment/about/call-for-papers',
                'type': 'elsevier'
            },
            {
                'name': 'Cities',
                'url': 'https://www.sciencedirect.com/journal/cities/about/call-for-papers',
                'type': 'elsevier'
            }
        ]

    def scrape_elsevier_journal(self, journal_info: Dict) -> List[Dict]:
        """Scrape special issues from Elsevier journals"""
        special_issues = []
        
        try:
            print(f"Scraping {journal_info['name']}...")
            response = requests.get(journal_info['url'], headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find special issue sections
                # Note: Elsevier's HTML structure may vary, adjust selectors as needed
                issue_sections = soup.find_all(['div', 'section'], class_=lambda x: x and ('special' in x.lower() or 'call' in x.lower()))
                
                if not issue_sections:
                    # Try alternative method: look for headings and content
                    issue_sections = soup.find_all(['h2', 'h3', 'h4'])
                
                for section in issue_sections[:10]:  # Limit to first 10 to avoid noise
                    issue_data = self.extract_issue_info(section, journal_info['url'])
                    if issue_data:
                        special_issues.append(issue_data)
                
                print(f"Found {len(special_issues)} special issues for {journal_info['name']}")
            else:
                print(f"Failed to fetch {journal_info['name']}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"Error scraping {journal_info['name']}: {str(e)}")
        
        # Add delay to be respectful
        time.sleep(2)
        
        return special_issues

    def extract_issue_info(self, element, base_url: str) -> Dict:
        """Extract information from a special issue element"""
        try:
            # Try to find title
            title_elem = element if element.name in ['h2', 'h3', 'h4'] else element.find(['h2', 'h3', 'h4'])
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            
            # Skip if title is too short or generic
            if len(title) < 10 or title.lower() in ['special issues', 'call for papers', 'about']:
                return None
            
            # Try to find related content
            parent = element.parent if element.parent else element
            content = parent.get_text(strip=True)
            
            # Extract deadline (common patterns)
            deadline = self.extract_deadline(content)
            
            # Extract guest editors
            editors = self.extract_editors(content)
            
            # Extract description
            description = self.extract_description(content, title)
            
            # Try to find URL
            link = element.find('a') or parent.find('a')
            url = link.get('href') if link else base_url
            if url and not url.startswith('http'):
                url = 'https://www.sciencedirect.com' + url
            
            return {
                'title': title,
                'deadline': deadline,
                'guest_editors': editors,
                'description': description,
                'url': url
            }
        except:
            return None

    def extract_deadline(self, text: str) -> str:
        """Extract deadline from text"""
        import re
        
        # Common patterns for deadlines
        patterns = [
            r'deadline[:\s]+(\d{1,2}\s+\w+\s+\d{4})',
            r'due[:\s]+(\d{1,2}\s+\w+\s+\d{4})',
            r'submission[:\s]+(\d{1,2}\s+\w+\s+\d{4})',
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None

    def extract_editors(self, text: str) -> str:
        """Extract guest editors from text"""
        import re
        
        # Look for editor patterns
        patterns = [
            r'guest\s+editors?[:\s]+([^.]+)',
            r'editors?[:\s]+([A-Z][^.]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                editors = match.group(1).strip()
                # Clean up and limit length
                if len(editors) < 200:
                    return editors
        
        return None

    def extract_description(self, text: str, title: str) -> str:
        """Extract description from text"""
        # Remove title from text
        text = text.replace(title, '')
        
        # Get first substantial paragraph
        sentences = text.split('.')
        description = ''
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 50:  # Substantial sentence
                description = sentence + '.'
                break
        
        # Limit length
        if len(description) > 500:
            description = description[:497] + '...'
        
        return description if description else None

    def scrape_all(self) -> Dict:
        """Scrape all configured journals"""
        results = {
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'journals': []
        }
        
        for journal_info in self.journals:
            journal_data = {
                'name': journal_info['name'],
                'url': journal_info['url'],
                'special_issues': []
            }
            
            if journal_info['type'] == 'elsevier':
                journal_data['special_issues'] = self.scrape_elsevier_journal(journal_info)
            
            results['journals'].append(journal_data)
        
        return results

    def save_to_json(self, data: Dict, filepath: str):
        """Save scraped data to JSON file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Data saved to {filepath}")

def main():
    scraper = JournalScraper()
    data = scraper.scrape_all()
    
    # Save to data directory
    output_path = 'data/special_issues.json'
    scraper.save_to_json(data, output_path)
    
    print(f"\nScraping completed!")
    print(f"Total journals: {len(data['journals'])}")
    for journal in data['journals']:
        print(f"  - {journal['name']}: {len(journal['special_issues'])} special issues")

if __name__ == '__main__':
    main()
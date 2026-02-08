#!/usr/bin/env python3
"""
Academic Journal Special Issues Scraper using Playwright
Uses real browser automation for reliable scraping
"""

import json
import os
import asyncio
from datetime import datetime
from typing import List, Dict
from playwright.async_api import async_playwright
import re

class PlaywrightJournalScraper:
    def __init__(self):
        self.journals = [
            {
                'name': 'Remote Sensing of Environment',
                'url': 'https://www.sciencedirect.com/journal/remote-sensing-of-environment/about/call-for-papers',
                'backup_url': 'https://www.journals.elsevier.com/remote-sensing-of-environment/call-for-papers'
            },
            {
                'name': 'Cities',
                'url': 'https://www.sciencedirect.com/journal/cities/about/call-for-papers',
                'backup_url': 'https://www.journals.elsevier.com/cities/call-for-papers'
            }
        ]

    async def scrape_journal(self, page, journal_info: Dict) -> List[Dict]:
        """Scrape a single journal using Playwright"""
        special_issues = []
        
        try:
            print(f"📖 Scraping {journal_info['name']}...")
            
            # Try main URL first
            try:
                print(f"  → Visiting {journal_info['url']}")
                
                # Navigate with longer timeout
                await page.goto(journal_info['url'], wait_until='networkidle', timeout=60000)
                
                # Wait for content to load
                await page.wait_for_timeout(5000)  # Increased to 5 seconds
                
                # Scroll to load lazy content
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await page.wait_for_timeout(2000)
                
                # Extract special issues from the page
                issues = await self.extract_special_issues(page, journal_info['url'])
                
                if issues:
                    special_issues.extend(issues)
                    print(f"  ✓ Found {len(issues)} special issues")
                else:
                    print(f"  ⚠ No issues found, trying backup URL...")
                    # Try backup URL
                    if 'backup_url' in journal_info:
                        await page.goto(journal_info['backup_url'], wait_until='networkidle', timeout=60000)
                        await page.wait_for_timeout(5000)
                        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                        await page.wait_for_timeout(2000)
                        
                        issues = await self.extract_special_issues(page, journal_info['backup_url'])
                        if issues:
                            special_issues.extend(issues)
                            print(f"  ✓ Found {len(issues)} special issues from backup")
                    
            except Exception as e:
                print(f"  ✗ Error accessing page: {str(e)[:100]}")
                
        except Exception as e:
            print(f"✗ Failed to scrape {journal_info['name']}: {str(e)[:100]}")
        
        return special_issues

    async def extract_special_issues(self, page, base_url: str) -> List[Dict]:
        """Extract special issues from the page"""
        issues = []
        
        try:
            # Get full page text for debugging
            full_text = await page.inner_text('body')
            print(f"  Page length: {len(full_text)} characters")
            
            # Method 1: Look for links containing "special" or "call"
            links = await page.query_selector_all('a')
            print(f"  Found {len(links)} total links on page")
            
            special_links = []
            for link in links:
                try:
                    href = await link.get_attribute('href')
                    text = await link.inner_text()
                    
                    if text and href:
                        text_lower = text.lower()
                        # Look for special issue indicators
                        if any(keyword in text_lower for keyword in ['special issue', 'call for papers', 'call for paper']):
                            special_links.append({
                                'text': text.strip(),
                                'href': href
                            })
                except:
                    continue
            
            print(f"  Found {len(special_links)} potential special issue links")
            
            # Extract from special links
            for link_info in special_links:
                # Try to find more context around this link
                try:
                    # Use the link text as title
                    title = link_info['text']
                    
                    # Skip generic titles
                    if len(title) < 15 or title.lower() in ['special issues', 'call for papers', 'view all']:
                        continue
                    
                    # Build URL
                    url = link_info['href']
                    if url.startswith('/'):
                        url = 'https://www.sciencedirect.com' + url
                    elif not url.startswith('http'):
                        url = base_url
                    
                    issue = {
                        'title': title,
                        'deadline': None,
                        'guest_editors': None,
                        'description': None,
                        'url': url
                    }
                    
                    issues.append(issue)
                    print(f"  ✓ Found: {title[:60]}...")
                    
                except Exception as e:
                    print(f"  Error processing link: {str(e)[:50]}")
                    continue
            
            # Method 2: Look for structured content blocks
            if not issues:
                print("  Trying alternative method: structured blocks...")
                
                # Look for div/section elements that might contain special issues
                blocks = await page.query_selector_all('div, section, article')
                
                for block in blocks[:50]:  # Limit to avoid too much processing
                    try:
                        text = await block.inner_text()
                        
                        # Check if this block mentions deadlines or special issues
                        if len(text) > 100 and len(text) < 5000:
                            if 'deadline' in text.lower() or 'special issue' in text.lower():
                                # Try to find a heading
                                heading = await block.query_selector('h1, h2, h3, h4, h5, strong, b')
                                
                                if heading:
                                    title = await heading.inner_text()
                                    
                                    if len(title) > 15 and len(title) < 200:
                                        issue = {
                                            'title': title.strip(),
                                            'deadline': self.extract_deadline(text),
                                            'guest_editors': self.extract_editors(text),
                                            'description': self.extract_description(text, title),
                                            'url': base_url
                                        }
                                        
                                        issues.append(issue)
                                        print(f"  ✓ Found via blocks: {title[:60]}...")
                    except:
                        continue
            
            # Method 3: Search for deadline patterns in full text
            if not issues:
                print("  Trying method 3: scanning full text for deadlines...")
                
                # Split text into paragraphs
                paragraphs = full_text.split('\n\n')
                
                for para in paragraphs:
                    if len(para) > 50 and 'deadline' in para.lower():
                        # Look for a title in this paragraph
                        lines = para.split('\n')
                        if lines:
                            title = lines[0].strip()
                            
                            if len(title) > 15 and len(title) < 200:
                                deadline = self.extract_deadline(para)
                                
                                if deadline:  # Only add if we found a deadline
                                    issue = {
                                        'title': title,
                                        'deadline': deadline,
                                        'guest_editors': self.extract_editors(para),
                                        'description': self.extract_description(para, title),
                                        'url': base_url
                                    }
                                    
                                    issues.append(issue)
                                    print(f"  ✓ Found via text scan: {title[:60]}...")
                        
        except Exception as e:
            print(f"  Error extracting issues: {str(e)}")
        
        # Deduplicate
        unique_issues = self.deduplicate_issues(issues)
        print(f"  → Total unique issues: {len(unique_issues)}")
        
        return unique_issues

    def extract_deadline(self, text: str) -> str:
        """Extract deadline from text"""
        patterns = [
            r'deadline[:\s]+(\d{1,2}\s+\w+\s+\d{4})',
            r'due[:\s]+(\d{1,2}\s+\w+\s+\d{4})',
            r'submission[:\s]+(\d{1,2}\s+\w+\s+\d{4})',
            r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)[a-z]*\s+\d{4})',
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None

    def extract_editors(self, text: str) -> str:
        """Extract guest editors from text"""
        patterns = [
            r'guest\s+editors?[:\s]+([A-Z][^.;]+(?:[,&]\s*[A-Z][^.;]+)*)',
            r'editors?[:\s]+([A-Z][^.;]+(?:[,&]\s*[A-Z][^.;]+)*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                editors = match.group(1).strip()
                # Clean up and limit length
                if len(editors) < 300 and not any(bad in editors.lower() for bad in ['deadline', 'submission', 'manuscript']):
                    return editors
        
        return None

    def extract_description(self, text: str, title: str) -> str:
        """Extract description from text"""
        # Remove title from text
        text = text.replace(title, '')
        
        # Get first substantial sentence
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        for sentence in sentences:
            # Skip sentences with keywords that suggest it's not a description
            if any(skip in sentence.lower() for skip in ['deadline', 'submission deadline', 'guest editor', 'email', 'doi']):
                continue
            
            if len(sentence) > 60 and len(sentence) < 600:  # Reasonable description length
                return (sentence + '.').strip()
        
        return None

    def deduplicate_issues(self, issues: List[Dict]) -> List[Dict]:
        """Remove duplicate issues based on title"""
        seen = set()
        unique = []
        
        for issue in issues:
            title_key = issue['title'].lower().strip()[:50]  # Use first 50 chars
            if title_key not in seen and len(title_key) > 15:
                seen.add(title_key)
                unique.append(issue)
        
        return unique

    async def scrape_all(self) -> Dict:
        """Scrape all journals using Playwright"""
        results = {
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'journals': []
        }
        
        async with async_playwright() as p:
            # Launch browser in headless mode
            browser = await p.chromium.launch(headless=True)
            
            # Create a new context with reasonable settings
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            for journal_info in self.journals:
                journal_data = {
                    'name': journal_info['name'],
                    'url': journal_info['url'],
                    'special_issues': []
                }
                
                # Scrape this journal
                issues = await self.scrape_journal(page, journal_info)
                journal_data['special_issues'] = issues
                
                results['journals'].append(journal_data)
                
                # Wait a bit between journals
                await asyncio.sleep(3)
            
            await browser.close()
        
        return results

    def save_to_json(self, data: Dict, filepath: str):
        """Save scraped data to JSON file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Data saved to {filepath}")

async def main():
    scraper = PlaywrightJournalScraper()
    
    print("=" * 60)
    print("🚀 Starting Playwright Journal Scraper")
    print("=" * 60)
    
    data = await scraper.scrape_all()
    
    # Save to data directory
    output_path = 'data/special_issues.json'
    scraper.save_to_json(data, output_path)
    
    print(f"\n{'=' * 60}")
    print(f"✅ Scraping completed!")
    print(f"{'=' * 60}")
    print(f"Total journals: {len(data['journals'])}")
    for journal in data['journals']:
        status = "✓" if len(journal['special_issues']) > 0 else "⚠"
        print(f"  {status} {journal['name']}: {len(journal['special_issues'])} special issues")
    print(f"{'=' * 60}\n")

if __name__ == '__main__':
    asyncio.run(main())

    
    def deduplicate_issues(self, issues: List[Dict]) -> List[Dict]:
        """Remove duplicate issues based on title"""
        seen = set()
        unique = []
        
        for issue in issues:
            title_key = issue['title'].lower().strip()
            if title_key not in seen:
                seen.add(title_key)
                unique.append(issue)
        
        return unique

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
    
    def get_fallback_data(self, journal_name: str) -> List[Dict]:
        """Get manually curated fallback data when scraping fails"""
        fallback_data = {
            'Remote Sensing of Environment': [
                {
                    'title': 'Remote Sensing of Ecohydrology',
                    'deadline': '31 March 2026',
                    'guest_editors': 'Hongliang Ma, Benjamin Dechant, Jiangyuan Zeng, Aleixandre Verger, William K. Smith, Youngryel Ryu',
                    'description': 'This special issue aims to highlight pioneering advancements in remote sensing of ecohydrology, fostering the exchange of leading-edge research and ideas on water-carbon coupling in terrestrial ecosystems.',
                    'url': 'https://www.sciencedirect.com/journal/remote-sensing-of-environment/about/call-for-papers'
                },
                {
                    'title': 'Large Area Monitoring with Landsat',
                    'deadline': '15 May 2026',
                    'guest_editors': 'Various Researchers',
                    'description': 'Focusing on generating essential large area datasets such as land cover, forest dynamics, phenology and evapotranspiration for addressing climate and land use challenges.',
                    'url': 'https://www.sciencedirect.com/journal/remote-sensing-of-environment/about/call-for-papers'
                }
            ],
            'Cities': [
                {
                    'title': 'The Politics of Spatial Inclusion in Cities',
                    'deadline': '28 February 2026',
                    'guest_editors': 'Rashid Mushkani, Robert J. Chaskin, Shin Koseki',
                    'description': 'This special issue examines the politics of spatial inclusion, exploring how land use, design, location, visibility, mobility, and enforcement distribute opportunities in urban spaces.',
                    'url': 'https://www.journals.elsevier.com/cities/call-for-papers'
                }
            ]
        }
        
        return fallback_data.get(journal_name, [])

    def scrape_all(self) -> Dict:
        """Scrape all configured journals"""
        results = {
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'journals': []
        }
        
        for journal_info in self.journals:
            journal_data = {
                'name': journal_info['name'],
                'url': journal_info['sources'][0]['url'] if 'sources' in journal_info else journal_info.get('url', ''),
                'special_issues': []
            }
            
            # Try scraping
            scraped_issues = self.scrape_elsevier_journal(journal_info)
            
            # Use fallback if scraping failed or returned no results
            if not scraped_issues and self.use_fallback:
                print(f"Using fallback data for {journal_info['name']}")
                scraped_issues = self.get_fallback_data(journal_info['name'])
            
            journal_data['special_issues'] = scraped_issues
            results['journals'].append(journal_data)
        
        return results

    def save_to_json(self, data: Dict, filepath: str):
        """Save scraped data to JSON file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\nData saved to {filepath}")

async def main():
    scraper = PlaywrightJournalScraper()
    
    print("=" * 60)
    print("🚀 Starting Playwright Journal Scraper")
    print("=" * 60)
    
    data = await scraper.scrape_all()
    
    # Save to data directory
    output_path = 'data/special_issues.json'
    scraper.save_to_json(data, output_path)
    
    print(f"\n{'=' * 60}")
    print(f"✅ Scraping completed!")
    print(f"{'=' * 60}")
    print(f"Total journals: {len(data['journals'])}")
    for journal in data['journals']:
        status = "✓" if len(journal['special_issues']) > 0 else "⚠"
        print(f"  {status} {journal['name']}: {len(journal['special_issues'])} special issues")
    print(f"{'=' * 60}\n")

if __name__ == '__main__':
    asyncio.run(main())
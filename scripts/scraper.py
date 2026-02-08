import os
import json
import requests
import time
from bs4 import BeautifulSoup
from datetime import datetime

# 👇 引入我们刚刚写的解析器工厂
from parsers import get_parser

API_KEY = os.environ.get('SCRAPER_API_KEY')

def load_journals():
    try:
        with open('data/journals.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Error: journals.json not found.")
        return []

def get_soup(target_url):
    if not API_KEY:
        print("❌ 缺少 API Key！")
        return None
    # ... (这里保持你原来的网络请求代码不变，省略以节省空间) ...
    # ... 记得把之前的 request 逻辑放这里 ...
    payload = { 'api_key': API_KEY, 'url': target_url, 'render': 'true' }
    try:
        for attempt in range(3):
            r = requests.get('http://api.scraperapi.com', params=payload, timeout=60)
            if r.status_code == 200: return BeautifulSoup(r.text, 'html.parser')
            time.sleep(2)
        return None
    except Exception as e:
        print(f"   ❌ Network Error: {e}")
        return None

def parse_journal(journal):
    print(f"📖 Scanning List: {journal['name']}...")
    soup = get_soup(journal['url'])
    issues = []
    if not soup: return []

    links = soup.select('a[href*="/special-issue/"]')
    print(f"   🔍 Found {len(links)} issues in list.")
    
    seen_urls = set()
    
    # 拿到针对该期刊的解析器函数！
    specific_parser = get_parser(journal['name'])

    for link in links[:5]: 
        title = link.get_text(strip=True)
        url = link.get('href')
        if not title or not url: continue
        if not url.startswith('http'): url = 'https://www.sciencedirect.com' + url
            
        if url not in seen_urls:
            seen_urls.add(url)
            print(f"      ☁️ Deep diving: {title[:30]}...")
            
            detail_soup = get_soup(url)
            
            # 👇 直接调用领到的解析器，不用管内部实现
            details = specific_parser(detail_soup)
            
            print(f"      🗓️ Deadline: {details['deadline']}")
            
            issues.append({
                'title': title,
                'url': url,
                'deadline': details['deadline'],
                'guest_editors': details['editors'],
                'description': details['description'],
                'last_updated': datetime.now().strftime('%Y-%m-%d')
            })
            
    return issues

def main():
    # ... (保持不变) ...
    print("=" * 60)
    print(f"🚀 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    journals = load_journals()
    if not journals: return

    results = {
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'journals': []
    }
    
    for journal in journals:
        issues = parse_journal(journal)
        journal_data = journal.copy()
        journal_data['special_issues'] = issues
        
        results['journals'].append(journal_data)
    
    os.makedirs('data', exist_ok=True)
    with open('data/issues.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print(f"💾 Data saved to data/issues.json")
    print("=" * 60)

if __name__ == "__main__":
    main()
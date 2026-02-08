import os
import json
import requests
import re
import time
from bs4 import BeautifulSoup
from datetime import datetime

# 从环境变量获取密钥
API_KEY = os.environ.get('SCRAPER_API_KEY')

def load_journals():
    try:
        with open('data/journals.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Error: data/journals.json not found.")
        return []

def get_soup(target_url):
    if not API_KEY:
        print("❌ 缺少 API Key！")
        return None

    payload = {
        'api_key': API_KEY,
        'url': target_url,
        'render': 'true', 
    }
    
    try:
        # 重试 3 次
        for attempt in range(3):
            r = requests.get('http://api.scraperapi.com', params=payload, timeout=60)
            if r.status_code == 200:
                return BeautifulSoup(r.text, 'html.parser')
            print(f"   ⚠️ Attempt {attempt+1} failed: {r.status_code}. Retrying...")
            time.sleep(2)
        return None
    except Exception as e:
        print(f"   ❌ Network Error: {e}")
        return None

def extract_details(soup):
    """
    从详情页提取：截止日期、责任编辑、简介
    """
    if not soup:
        return {"deadline": "Unknown", "editors": "Unknown", "description": ""}

    text_content = soup.get_text(" ", strip=True)
    
    # --- 1. 提取截止日期 ---
    deadline = "Check Detail"
    date_patterns = [
        r'Submission deadline:?\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})',
        r'deadline for manuscript submissions is\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})',
        r'submission deadline is\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})'
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text_content, re.IGNORECASE)
        if match:
            deadline = match.group(1)
            break
            
    # --- 2. 提取责任编辑 (Guest Editors) ---
    editors = "Unknown"
    # ScienceDirect 的编辑通常在 "Guest editors" 标题下
    # 我们尝试找包含 "Guest editors" 的元素，然后找它的兄弟节点或子节点
    try:
        # 方法 A: 简单的文本查找截取 (比较暴力但有效)
        editor_match = re.search(r'Guest editors?\s*:?\s*(.*?)(?=\s*(Submission|Manuscript|Inquiries|$))', text_content, re.IGNORECASE)
        if editor_match:
            editors_raw = editor_match.group(1).strip()
            # 截取前 100 个字符，防止抓到无关文本
            editors = editors_raw[:100] + "..." if len(editors_raw) > 100 else editors_raw
    except:
        pass

    # --- 3. 提取简介/详细介绍 ---
    description = ""
    try:
        # 尝试寻找正文区域，ScienceDirect 结构多变，这里取网页主要文本
        # 移除 script 和 style
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # 获取清洗后的文本
        clean_text = soup.get_text(" ", strip=True)
        # 简单清洗：找到 "Call for papers" 或标题之后的内容
        # 这里做一个简单的切片，保留前 500 个字符作为简介
        description = clean_text[:500] + "..."
    except:
        description = "No description extracted."

    return {
        "deadline": deadline,
        "editors": editors,
        "description": description
    }

def parse_journal(journal):
    print(f"📖 Scanning List: {journal['name']}...")
    soup = get_soup(journal['url'])
    issues = []
    
    if not soup: return []

    links = soup.select('a[href*="/special-issue/"]')
    print(f"   🔍 Found {len(links)} issues in list.")

    seen_urls = set()
    
    # ⚠️ 注意：为了测试，我这里还是限制抓取前 5 个
    # 如果要全抓，请去掉 [:5]
    for link in links[:5]: 
        title = link.get_text(strip=True)
        url = link.get('href')
        
        if not title or not url: continue
        if not url.startswith('http'): url = 'https://www.sciencedirect.com' + url
            
        if url not in seen_urls:
            seen_urls.add(url)
            print(f"      ☁️ Deep diving: {title[:30]}...")
            
            # 进入详情页
            detail_soup = get_soup(url)
            
            # 提取所有详情
            details = extract_details(detail_soup)
            
            print(f"      🗓️ Deadline: {details['deadline']}")
            print(f"      👥 Editors: {details['editors'][:30]}...")
            
            issues.append({
                'title': title,
                'url': url,
                'deadline': details['deadline'],
                'guest_editors': details['editors'],   # 新增字段
                'description': details['description'], # 新增字段
                'last_updated': datetime.now().strftime('%Y-%m-%d')
            })
            
    return issues

def main():
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
        results['journals'].append({
            'name': journal['name'],
            'url': journal['url'],
            'special_issues': issues
        })
    
    os.makedirs('data', exist_ok=True)
    with open('data/issues.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print(f"💾 Data saved to data/issues.json")
    print("=" * 60)

if __name__ == "__main__":
    main()
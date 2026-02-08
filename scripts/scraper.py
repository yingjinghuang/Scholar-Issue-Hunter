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
    通用状态机解析器：适配 RSE 和 Cities 等不同排版结构
    """
    if not soup:
        return {"deadline": "Unknown", "editors": "Unknown", "description": ""}

    # --- 1. 全局大清洗 (保持不变) ---
    for tag in soup(["header", "footer", "nav", "script", "style", "noscript", "iframe", ".banner", ".cookie-notice", ".submit-search-button-wrap"]):
        tag.decompose()

    full_text = soup.get_text(" ", strip=True)

    # --- 2. 提取截止日期 (最稳的锚点) ---
    deadline = "Check Detail"
    deadline_node = None
    
    # 尝试寻找包含 "Submission deadline" 的节点
    # 这是一个关键锚点，我们随后会从这个位置开始往下一行一行读
    try:
        target_str = re.compile("Submission deadline", re.IGNORECASE)
        deadline_node = soup.find(string=target_str)
        
        if deadline_node:
            # 获取日期文本
            parent = deadline_node.parent
            # 如果是在 strong 标签里
            strong = parent.find("strong")
            if strong:
                deadline = strong.get_text(strip=True)
            else:
                # 否则取冒号后面的文字
                deadline = parent.get_text(strip=True).split(":")[-1].strip()
            
            # 将锚点提升到块级元素 (div 或 p)，以便查找兄弟节点
            deadline_node = parent.find_parent(['div', 'p'])
    except:
        pass

    # --- 3. 流式提取 (State Machine) ---
    editors_parts = []
    description_parts = []
    
    # 初始状态：默认为 "description" (因为 Cities 把简介放在最前面)
    # 状态枚举: 'description', 'editors', 'stop'
    current_mode = 'description' 

    if deadline_node:
        # 获取 deadline 之后的所有同级元素
        siblings = deadline_node.find_next_siblings()
        
        for tag in siblings:
            text = tag.get_text(strip=True)
            text_lower = text.lower()

            # --- A. 状态切换检查 ---
            
            # 1. 遇到 "Guest editors" -> 切换到编辑模式
            if "guest editors" in text_lower and len(text) < 50: # 长度限制防止误判正文
                current_mode = 'editors'
                continue # 跳过标题本身

            # 2. 遇到 "Special issue information" -> 切换回简介模式
            if "special issue information" in text_lower and len(text) < 100:
                current_mode = 'description'
                continue

            # 3. 遇到 "Manuscript submission" 或 "Keywords" -> 停止解析
            if "manuscript submission" in text_lower or "keywords:" in text_lower:
                break

            # --- B. 数据收集 ---
            
            if current_mode == 'editors':
                # 过滤空行
                if len(text) > 2:
                    # Cities 的编辑在 div 里，RSE 在 p 里，这里都兼容
                    # 简单清洗：移除 "Email:" 这种干扰词
                    clean_editor = text.replace("Email:", "").strip()
                    editors_parts.append(clean_editor)

            elif current_mode == 'description':
                # 只收集段落和列表，忽略太短的垃圾字符
                if tag.name in ['p', 'ul', 'ol', 'div'] and len(text) > 10:
                    # 移除内联样式，保留 HTML 结构 (为了换行和列表)
                    del tag['style']
                    del tag['class']
                    # 移除内部的链接 (避免点进去跳出)
                    for a in tag.find_all('a'):
                        a.unwrap() # 保留文字，移除 <a> 标签
                        
                    description_parts.append(str(tag))

    # --- 4. 数据组装 ---
    
    # 编辑：用换行符连接
    editors_str = "<br>".join(editors_parts) if editors_parts else "Editors info not found."
    
    # 简介：拼接 HTML
    description_html = "".join(description_parts)
    if not description_html:
        description_html = "Detailed description available on the official website."

    return {
        "deadline": deadline,
        "editors": editors_str, 
        "description": description_html
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
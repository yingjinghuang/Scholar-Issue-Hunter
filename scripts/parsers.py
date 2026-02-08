import re
from bs4 import BeautifulSoup

# =========================================================
# 🛠️ 通用工具函数
# =========================================================

def clean_html_attributes(html_content):
    """
    清洗 HTML: 
    1. 移除 span/div/font 等无语义标签 (unwrap)
    2. 保留 p/ul/li 等结构标签，但移除 class/style (attrs={})
    """
    if not html_content: return ""
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 1. 拆包无语义标签
    for tag in soup.find_all(['span', 'div', 'font', 'strong', 'b', 'em', 'i']):
        tag.unwrap()
        
    # 2. 清洗保留标签的属性
    valid_tags = ['p', 'ul', 'ol', 'li', 'br']
    for tag in soup.find_all(valid_tags):
        tag.attrs = {} 
        
    # 3. 移除其他不支持的标签
    for tag in soup.find_all():
        if tag.name not in valid_tags:
            tag.unwrap()

    # 4. 移除空标签
    for tag in soup.find_all():
        if len(tag.get_text(strip=True)) == 0:
            tag.decompose()
            
    return str(soup).strip()

def extract_pure_name(text):
    text = text.replace('&nbsp;', ' ').strip()
    text = re.sub(r'\s+', ' ', text)

    stop_indicators = [
        'Department', 'University', 'School', 'Institute', 'Center', 'Centre', 
        'College', 'Faculty', 'Lead', 'Principal', 'Chair', 'Lecturer', 'Reader',
        'Email', ' at ', ' of ', 'Head', 
        'Affiliation', 'Areas', 'Expertise', 'Interests'
    ]
    
    for word in stop_indicators:
        idx = text.lower().find(word.lower())
        if idx != -1:
            if idx < 3: return "" 
            text = text[:idx]

    if ',' in text:
        text = text.split(',')[0]

    text = re.sub(r'\b(Dr\.|Dr|Prof\.|Prof|Professor|Associate|Assistant)\b\.?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+(Professor|Prof|Lecturer|Reader|Chair)\b', '', text, flags=re.IGNORECASE)
    
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '', text)
    text = text.strip(" ,.-:")
    
    return text.strip()

def is_metadata_line(text):
    text_lower = text.lower()
    if "submission deadline" in text_lower and len(text) < 100:
        return True
    if len(text) < 30 and re.search(r'\d{1,2}\s+[A-Za-z]+\s+\d{4}', text):
        return True
    return False

# =========================================================
# 1. Cities 专用解析器
# =========================================================
def parse_cities_sciencedirect(soup):
    if not soup: return default_fallback()

    # A. Deadline
    deadline = "Check Link"
    try:
        text = soup.get_text(" ", strip=True)
        date_match = re.search(r'(?:Submission deadline|Deadline):?\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})', text, re.IGNORECASE)
        if date_match: deadline = date_match.group(1)
    except: pass

    # B. Description
    description_parts = []
    start_node = soup.find(lambda tag: tag.name in ['h2', 'h3'] and "Call for papers" in tag.get_text())
    
    if start_node:
        for tag in start_node.find_all_next(['p', 'ul', 'div']):
            if tag.find(['p', 'ul', 'div']): continue 

            text = tag.get_text(strip=True)
            if "guest editors" in text.lower(): continue 
            if "manuscript submission" in text.lower(): break
            if "university" in text.lower(): continue
            if is_metadata_line(text): continue
            if len(text) < 10: continue
            
            # 🔥 关键修改：如果是 div，强制转为 p
            if tag.name == 'div':
                tag.name = 'p'

            tag.attrs = {} 
            for a in tag.find_all('a'): a.unwrap()
            description_parts.append(str(tag))

    # C. Editors
    editors_parts = []
    editor_divs = soup.find_all('div', class_='OutlineElement')
    
    for div in editor_divs:
        text = div.get_text(strip=True)
        if "submit" in text.lower() or "guide" in text.lower(): continue
        
        if len(text) > 2 and "guest editors" not in text.lower():
            pure_name = extract_pure_name(text)
            if len(pure_name) > 2 and len(pure_name) < 40: 
                editors_parts.append(pure_name)

    return {
        "deadline": deadline,
        "editors": "<br>".join(editors_parts) if editors_parts else "See website",
        "description": clean_html_attributes("".join(description_parts))
    }

# =========================================================
# 2. RSE / BAE 兼容解析器
# =========================================================
def parse_rse_sciencedirect(soup):
    if not soup: return default_fallback()

    # 清洗
    for tag in soup(["header", "footer", "nav", "script", "style", "noscript", ".banner", ".cookie-notice"]):
        tag.decompose()

    # 日期
    full_text = soup.get_text(" ", strip=True)
    deadline = "Check Link"
    date_match = re.search(r'(?:Submission deadline|Deadline):?\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})', full_text, re.IGNORECASE)
    if date_match: deadline = date_match.group(1)

    # 扫描
    editors_parts = []
    description_parts = []
    current_state = 'description'
    
    container = soup.find('div', class_='inner') or soup.find('main') or soup.body
    if not container: return default_fallback()

    elements = container.find_all_next(['p', 'div', 'ul', 'ol', 'h3'])
    
    for tag in elements:
        if tag.find(['p', 'div', 'ul', 'ol']): continue 
        
        text = tag.get_text(" ", strip=True)
        text_lower = text.lower()
        if len(text) < 3: continue
        
        if "manuscript submission" in text_lower or "keywords:" in text_lower: break
        
        if "guest editors" in text_lower and len(text) < 100:
            current_state = 'editors'
            continue
        if ("special issue info" in text_lower or "aims and scope" in text_lower) and len(text) < 100:
            current_state = 'description'
            continue
        if "science direct" in text_lower: continue

        if current_state == 'editors':
            if len(text) < 300:
                pure_name = extract_pure_name(text)
                if pure_name and "@" not in pure_name and len(pure_name) > 2:
                    editors_parts.append(pure_name)
                    
        elif current_state == 'description':
            if is_metadata_line(text): continue

            if tag.name in ['p', 'ul', 'ol', 'div']:
                if tag.name == 'div' and len(text) < 30: continue
                
                # 🔥 关键修改：把 div 变成 p，这样 clean_html 就不会删掉它了
                if tag.name == 'div':
                    tag.name = 'p'
                
                tag.attrs = {}
                for a in tag.find_all('a'): a.unwrap()
                description_parts.append(str(tag))

    unique_editors = list(dict.fromkeys(editors_parts))

    return {
        "deadline": deadline,
        "editors": "<br>".join(unique_editors) if unique_editors else "See website",
        "description": clean_html_attributes("".join(description_parts))
    }

def default_fallback():
    return {"deadline": "Unknown", "editors": "Unknown", "description": ""}

# =========================================================
# 3. 路由器
# =========================================================
def get_parser(journal_name):
    name_lower = journal_name.lower()
    
    if "cities" in name_lower:
        print(f"      ⚙️ Using Parser: Cities Specific")
        return parse_cities_sciencedirect
    
    elif "remote sensing" in name_lower or "building and environment" in name_lower:
        print(f"      ⚙️ Using Parser: Standard (RSE/BAE)")
        return parse_rse_sciencedirect
        
    else:
        print(f"      ⚠️ New Journal Detected. Fallback to RSE Logic.")
        return parse_rse_sciencedirect
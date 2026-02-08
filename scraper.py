#!/usr/bin/env python3
import json
import os
import asyncio
import re
from datetime import datetime
from typing import List, Dict
from playwright.async_api import async_playwright

# 兼容性处理：适配不同版本的 playwright-stealth
try:
    from playwright_stealth import stealth_async
except ImportError:
    async def stealth_async(page):
        import playwright_stealth
        await playwright_stealth.stealth_async(page)

class PlaywrightJournalScraper:
    def __init__(self):
        # 使用你提供源码的 ScienceDirect 目标页面
        self.journals = [
            {
                'name': 'Remote Sensing of Environment',
                'url': 'https://www.sciencedirect.com/journal/remote-sensing-of-environment/about/call-for-papers'
            },
            {
                'name': 'Cities',
                'url': 'https://www.sciencedirect.com/journal/cities/about/call-for-papers'
            }
        ]

    async def scrape_journal(self, context, journal_info: Dict) -> List[Dict]:
        page = await context.new_page()
        await stealth_async(page)
        
        issues = []
        try:
            print(f"📖 Scraping {journal_info['name']}...")
            # 1. 访问页面
            await page.goto(journal_info['url'], wait_until='domcontentloaded', timeout=60000)
            
            # 2. 关键：等待数据列表容器渲染完成 (基于你提供的源码类名)
            try:
                await page.wait_for_selector('li.list-item', timeout=20000)
                # 额外缓冲，确保 React 列表渲染完整
                await asyncio.sleep(2) 
            except:
                print(f"   ⚠ Timeout: 'li.list-item' not found. Page might be empty or loading too slow.")

            # 3. 滚动以触发可能的懒加载
            await page.mouse.wheel(0, 1000)
            await asyncio.sleep(1)

            # 4. 执行抓取逻辑
            issues = await self.extract_logic(page)
            print(f"   ✓ Success: Found {len(issues)} special issues")

        except Exception as e:
            print(f"   ✗ Error scraping {journal_info['name']}: {str(e)[:100]}")
        finally:
            await page.close()
        
        return issues

    async def extract_logic(self, page) -> List[Dict]:
        """针对 ScienceDirect HTML 结构的精准提取"""
        scraped_data = []
        
        # 定位所有的列表条目
        items = await page.query_selector_all('li.list-item')
        
        for item in items:
            try:
                # A. 提取标题和 URL (基于源码: a.anchor.title)
                title_link = await item.query_selector('h3 a.anchor.title')
                if not title_link:
                    continue
                
                title = await title_link.inner_text()
                href = await title_link.get_attribute('href')
                
                # B. 提取截止日期 (基于源码: div.text-xs)
                deadline = "Not specified"
                deadline_elem = await item.query_selector('div.text-xs')
                if deadline_elem:
                    deadline_text = await deadline_elem.inner_text()
                    # 正则匹配日期部分
                    match = re.search(r'deadline:\s*(.*)', deadline_text, re.IGNORECASE)
                    if match:
                        deadline = match.group(1).strip()

                # C. 提取客座编辑 (基于源码: p.summary)
                editors = "Not specified"
                editor_elem = await item.query_selector('p.summary')
                if editor_elem:
                    editor_text = await editor_elem.inner_text()
                    editors = editor_text.replace('Guest editors:', '').strip()

                # 补全 URL
                full_url = href if href.startswith('http') else 'https://www.sciencedirect.com' + href

                scraped_data.append({
                    'title': title.strip(),
                    'url': full_url,
                    'deadline': deadline,
                    'guest_editors': editors,
                    'last_updated': datetime.now().strftime('%Y-%m-%d')
                })
            except:
                continue
                
        # 如果 li 抓取失败，启动方案 B：直接抓取所有 SI 链接
        if not scraped_data:
            print("   🔍 Falling back to Link-based scan...")
            all_si_links = await page.query_selector_all('a[href*="/special-issue/"]')
            for link in all_si_links:
                try:
                    t = await link.inner_text()
                    u = await link.get_attribute('href')
                    if len(t) > 15:
                        scraped_data.append({
                            'title': t.strip(),
                            'url': u if u.startswith('http') else 'https://www.sciencedirect.com' + u,
                            'deadline': "See link",
                            'guest_editors': "See link",
                            'last_updated': datetime.now().strftime('%Y-%m-%d')
                        })
                except: continue

        return self.deduplicate(scraped_data)

    def deduplicate(self, issues: List[Dict]) -> List[Dict]:
        seen = set()
        unique = []
        for i in issues:
            key = i['title'].lower().strip()
            if key not in seen:
                seen.add(key)
                unique.append(i)
        return unique

    async def run(self):
        print("=" * 60)
        print(f"🚀 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        results = {
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'journals': []
        }
        
        async with async_playwright() as p:
            # 必须使用 chromium 并在 headless 模式下配置真实的上下文
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            
            for journal in self.journals:
                issues = await self.scrape_journal(context, journal)
                results['journals'].append({
                    'name': journal['name'],
                    'url': journal['url'],
                    'special_issues': issues
                })
                # 礼貌性延迟，防止 IP 触发二次拦截
                await asyncio.sleep(5)

            await browser.close()
            
        # 保存结果
        os.makedirs('data', exist_ok=True)
        with open('data/special_issues.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Scraping completed. Data saved to data/special_issues.json")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(PlaywrightJournalScraper().run())
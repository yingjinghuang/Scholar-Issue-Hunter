#!/usr/bin/env python3
import json
import os
import asyncio
from datetime import datetime
from typing import List, Dict
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import re

class PlaywrightJournalScraper:
    def __init__(self):
        # 移除了容易被封锁的 sciencedirect 直接链接，改用 Elsevier 专门的列表页
        self.journals = [
            {
                'name': 'Remote Sensing of Environment',
                'url': 'https://www.journals.elsevier.com/remote-sensing-of-environment/call-for-papers'
            },
            {
                'name': 'Cities',
                'url': 'https://www.journals.elsevier.com/cities/call-for-papers'
            }
        ]

    async def scrape_journal(self, context, journal_info: Dict) -> List[Dict]:
        page = await context.new_page()
        # 应用 Stealth 插件隐藏 Playwright 特征
        await stealth_async(page)
        
        special_issues = []
        try:
            print(f"📖 Scraping {journal_info['name']}...")
            
            # 模拟真实浏览器行为
            await page.goto(journal_info['url'], wait_until='networkidle', timeout=60000)
            
            # 模拟人类缓慢滚动页面，触发懒加载内容
            for _ in range(3):
                await page.mouse.wheel(0, 800)
                await asyncio.sleep(1)

            # 获取页面内容长度，用于排查是否被拦截
            content_length = len(await page.content())
            print(f"   Page content length: {content_length} characters")

            if content_length < 2000:
                print(f"   ⚠ Warning: Content too short. Might be blocked by bot detection.")

            # 提取逻辑
            special_issues = await self.extract_logic(page)
            print(f"   ✓ Found {len(special_issues)} issues")

        except Exception as e:
            print(f"   ✗ Error: {str(e)[:100]}")
        finally:
            await page.close()
        
        return special_issues

    async def extract_logic(self, page) -> List[Dict]:
        """针对 Elsevier 期刊列表页的结构化提取"""
        issues = []
        
        # 策略 1: 寻找典型的文章卡片结构
        # Elsevier 列表页通常使用 <h3> 或 <a> 带有特定的 title
        selectors = [
            'a[data-testid="article-list-title-link"]', 
            'div.pod-listing-header a',
            'h3'
        ]
        
        found_elements = []
        for selector in selectors:
            elements = await page.query_selector_all(selector)
            if elements:
                found_elements = elements
                break

        for el in found_elements:
            try:
                title = await el.inner_text()
                href = await el.get_attribute('href')
                
                # 过滤无关链接
                title_lower = title.lower().strip()
                if len(title_lower) < 15 or any(x in title_lower for x in ['cookies', 'privacy', 'terms', 'guide for authors']):
                    continue

                # 寻找日期/截止日期 (在父级或后续元素中)
                parent = await el.query_selector('xpath=..') # 获取父节点
                parent_text = await parent.inner_text() if parent else ""
                
                deadline = self.parse_deadline(parent_text)
                
                issues.append({
                    'title': title.strip(),
                    'url': href if href.startswith('http') else 'https://www.journals.elsevier.com' + href,
                    'deadline': deadline,
                    'last_seen': datetime.now().strftime('%Y-%m-%d')
                })
            except:
                continue
                
        return self.deduplicate(issues)

    def parse_deadline(self, text: str) -> str:
        # 匹配常用的日期格式
        pattern = r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})'
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1) if match else "Not specified"

    def deduplicate(self, issues: List[Dict]) -> List[Dict]:
        seen = set()
        unique = []
        for i in issues:
            if i['title'].lower() not in seen:
                seen.add(i['title'].lower())
                unique.append(i)
        return unique

    async def run(self):
        results = {
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'journals': []
        }
        
        async with async_playwright() as p:
            # 关键：使用真实的 User-Agent
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            )
            
            for journal in self.journals:
                issues = await self.scrape_journal(context, journal)
                results['journals'].append({
                    'name': journal['name'],
                    'count': len(issues),
                    'special_issues': issues
                })
                await asyncio.sleep(5) # 频率控制

            await browser.close()
            
        # 存入文件
        os.makedirs('data', exist_ok=True)
        with open('data/special_issues.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n✅ All done. Results saved to data/special_issues.json")

if __name__ == "__main__":
    asyncio.run(PlaywrightJournalScraper().run())
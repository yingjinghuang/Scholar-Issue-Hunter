import os
import sys
from bs4 import BeautifulSoup
import scraper as scraper
from parsers import get_parser # 引入解析器

def test_single_url(url, journal_name):
    print(f"\n🔎 Testing for Journal: {journal_name}...")
    print(f"   URL: {url}")
    
    # 1. 模拟网络请求
    # soup = scraper.get_soup(url) # 如果你想跑真实网络
    # 或者读取本地文件：

    with open(url, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    # 2. 获取对应的解析器
    parser_func = get_parser(journal_name)
    
    # 3. 运行解析
    details = parser_func(soup)
    
    print("\n   ------ PARSED RESULT ------")
    print(f"   🗓️  Deadline:    {details['deadline']}")
    print(f"   👥 Editors:     {details['editors'][:100]}...") 
    print(f"   📝 Description: {details['description'][:100]}...")

if __name__ == "__main__":
    # 此时需要你在根目录下有 rse.html 和 cities.html
    test_single_url("test_data/cities.html", "Cities")
    test_single_url("test_data/rse.html", "Remote Sensing of Environment")
    test_single_url("test_data/bae.html", "Building and Environment")
    test_single_url("test_data/ceus.html", "Computers, Environment and Urban Systems")
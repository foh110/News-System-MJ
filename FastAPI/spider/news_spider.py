"""
新闻爬虫模块
支持从主流新闻源自动采集新闻并入库
"""
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
import asyncio
import re
from urllib.parse import urljoin


class NewsSpider:
    """新闻爬虫基类"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
    
    async def fetch_page(self, url: str) -> Optional[str]:
        """异步获取网页内容"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                response.encoding = response.apparent_encoding
                return response.text
        except Exception as e:
            print(f"抓取失败 {url}: {e}")
            return None
    
    def clean_html(self, html: str) -> str:
        """清理HTML标签，提取纯文本"""
        if not html:
            return ""
        soup = BeautifulSoup(html, 'html.parser')
        # 移除脚本和样式
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator='\n', strip=True)
        # 清理多余空白
        text = re.sub(r'\n+', '\n', text)
        return text.strip()


class SinaNewsSpider(NewsSpider):
    """新浪新闻爬虫"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://news.sina.com.cn"
        self.category_map = {
            1: "https://news.sina.com.cn/china/",      # 国内
            2: "https://news.sina.com.cn/world/",      # 国际
            3: "https://tech.sina.com.cn/",            # 科技
            4: "https://sports.sina.com.cn/",          # 体育
            5: "https://finance.sina.com.cn/"          # 财经
        }
    
    async def crawl_category(self, category_id: int, max_pages: int = 3) -> List[Dict]:
        """抓取指定分类的新闻"""
        if category_id not in self.category_map:
            return []
        
        news_list = []
        base_url = self.category_map[category_id]
        
        for page in range(1, max_pages + 1):
            # 新浪新闻列表页URL规则
            list_url = f"{base_url}index.shtml" if page == 1 else f"{base_url}index_{page}.shtml"
            html = await self.fetch_page(list_url)
            
            if not html:
                continue
            
            soup = BeautifulSoup(html, 'html.parser')
            # 提取新闻链接（根据实际DOM结构调整选择器）
            articles = soup.select('a[href*="/a/"]') or soup.select('h2 a') or soup.select('.news-item a')
            
            for article in articles[:20]:  # 每页最多20条
                link = article.get('href', '')
                title = article.get_text(strip=True)
                
                if not link or not title or len(title) < 5:
                    continue
                
                # 补全URL
                if not link.startswith('http'):
                    link = urljoin(self.base_url, link)
                
                # 抓取详情页
                news_item = await self.crawl_detail(link, category_id, title)
                if news_item:
                    news_list.append(news_item)
            
            await asyncio.sleep(2)  # 礼貌爬取，避免被封
        
        return news_list
    
    async def crawl_detail(self, url: str, category_id: int, title: str) -> Optional[Dict]:
        """抓取新闻详情"""
        html = await self.fetch_page(url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 提取内容（根据新浪实际DOM结构调整）
        content_div = soup.select_one('.article-content') or soup.select_one('#artibody') or soup.select_one('.content')
        if not content_div:
            return None
        
        content = self.clean_html(str(content_div))
        if len(content) < 50:  # 内容太短，跳过
            return None
        
        # 提取作者和发布时间
        author = ""
        publish_time = datetime.now()
        
        author_div = soup.select_one('.source') or soup.select_one('.time-source')
        if author_div:
            author_text = author_div.get_text(strip=True)
            # 尝试提取作者名
            author_match = re.search(r'([\u4e00-\u9fa5]{2,4})$', author_text)
            if author_match:
                author = author_match.group(1)
        
        # 提取封面图
        image = ""
        img_tag = soup.select_one('.img-wrapper img') or soup.select_one('#topVarMedia img')
        if img_tag:
            image = img_tag.get('src', '')
        
        return {
            'title': title[:250],
            'description': content[:200] + '...' if len(content) > 200 else content,
            'content': content,
            'image': image,
            'author': author or '新浪新闻',
            'category_id': category_id,
            'source_url': url,
            'publish_time': publish_time
        }


class TencentNewsSpider(NewsSpider):
    """腾讯新闻爬虫"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://news.qq.com"
        self.category_map = {
            1: "https://i.news.qq.com/web/guest/index.htm#/hot",      # 热点
            2: "https://i.news.qq.com/web/guest/index.htm#/world",    # 国际
            3: "https://tech.qq.com/",                                 # 科技
        }
    
    async def crawl_category(self, category_id: int, max_pages: int = 2) -> List[Dict]:
        """腾讯新闻主要通过API获取，这里使用备用方案"""
        # 腾讯新闻反爬较严，建议使用其开放API或RSS
        return []


class NewsCrawlerManager:
    """爬虫管理器"""
    
    def __init__(self):
        self.spiders = {
            'sina': SinaNewsSpider(),
        }
    
    async def crawl_all(self, category_ids: List[int] = None) -> Dict:
        """抓取所有分类的新闻"""
        if category_ids is None:
            category_ids = [1, 2, 3]  # 默认抓取国内、国际、科技
        
        all_news = []
        
        for category_id in category_ids:
            # 使用新浪爬虫
            sina_spider = SinaNewsSpider()
            news_list = await sina_spider.crawl_category(category_id, max_pages=2)
            all_news.extend(news_list)
        
        # 去重（基于标题）
        unique_news = self.deduplicate_news(all_news)
        
        return {
            'total': len(all_news),
            'unique': len(unique_news),
            'news': unique_news
        }
    
    def deduplicate_news(self, news_list: List[Dict]) -> List[Dict]:
        """基于标题去重"""
        seen_titles = set()
        unique_news = []
        
        for news in news_list:
            title_key = news['title'][:50]  # 取前50字符作为唯一标识
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_news.append(news)
        
        return unique_news

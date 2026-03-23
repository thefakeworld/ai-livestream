#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
News Fetcher Module - 新闻抓取模块
从多个来源抓取热点新闻
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import hashlib

import requests
import feedparser
from bs4 import BeautifulSoup
from loguru import logger

from config import NEWS_SOURCES, NEWS_CACHE_DIR, NEWS_COUNT_PER_FETCH


class NewsItem:
    """新闻条目类"""
    def __init__(self, title: str, content: str, source: str, url: str, pub_date: str = ""):
        self.title = title
        self.content = content
        self.source = source
        self.url = url
        self.pub_date = pub_date
        self.id = hashlib.md5(f"{title}{source}".encode()).hexdigest()[:8]
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "source": self.source,
            "url": self.url,
            "pub_date": self.pub_date
        }
    
    def to_tts_text(self) -> str:
        """转换为TTS可读的文本格式"""
        return f"{self.title}。{self.content}"
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'NewsItem':
        return cls(
            title=data["title"],
            content=data["content"],
            source=data["source"],
            url=data["url"],
            pub_date=data.get("pub_date", "")
        )


class NewsFetcher:
    """新闻抓取器"""
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }
        self.cache_file = NEWS_CACHE_DIR / "news_cache.json"
        self._load_cache()
    
    def _load_cache(self):
        """加载缓存的新闻"""
        self.cached_news: List[NewsItem] = []
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cached_news = [NewsItem.from_dict(item) for item in data]
                logger.info(f"已加载 {len(self.cached_news)} 条缓存新闻")
            except Exception as e:
                logger.error(f"加载新闻缓存失败: {e}")
    
    def _save_cache(self):
        """保存新闻到缓存"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump([item.to_dict() for item in self.cached_news], f, ensure_ascii=False, indent=2)
            logger.info(f"已保存 {len(self.cached_news)} 条新闻到缓存")
        except Exception as e:
            logger.error(f"保存新闻缓存失败: {e}")
    
    def fetch_from_rss(self, rss_url: str) -> List[NewsItem]:
        """从RSS源抓取新闻"""
        news_items = []
        try:
            response = requests.get(rss_url, headers=self.headers, timeout=10)
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries[:NEWS_COUNT_PER_FETCH]:
                title = entry.get('title', '无标题')
                summary = entry.get('summary', '')
                
                # 清理HTML标签
                if summary:
                    soup = BeautifulSoup(summary, 'html.parser')
                    content = soup.get_text().strip()
                else:
                    content = title
                
                # 截断过长的内容
                if len(content) > 500:
                    content = content[:500] + "..."
                
                news_item = NewsItem(
                    title=title,
                    content=content,
                    source=feed.feed.get('title', 'RSS'),
                    url=entry.get('link', ''),
                    pub_date=entry.get('published', '')
                )
                news_items.append(news_item)
            
            logger.info(f"从RSS {rss_url} 获取了 {len(news_items)} 条新闻")
        except Exception as e:
            logger.error(f"从RSS {rss_url} 抓取失败: {e}")
        
        return news_items
    
    def fetch_from_google_news(self, query: str = "热点新闻") -> List[NewsItem]:
        """从Google News抓取新闻"""
        news_items = []
        try:
            # Google News RSS
            url = f"https://news.google.com/rss/search?q={query}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
            news_items = self.fetch_from_rss(url)
        except Exception as e:
            logger.error(f"从Google News抓取失败: {e}")
        return news_items
    
    def fetch_from_baidu_hot(self) -> List[NewsItem]:
        """从百度热搜抓取（备用方案，使用模拟数据）"""
        # 由于直接访问百度热搜有反爬机制，这里使用备用数据源
        hot_topics = [
            "科技领域最新动态：人工智能技术持续突破，各大科技公司纷纷布局",
            "经济形势分析：全球经济复苏态势良好，市场信心逐步恢复",
            "社会热点关注：环保议题持续升温，可持续发展成为共识",
            "文化娱乐资讯：国产电影票房持续走高，文化产业发展势头强劲",
            "体育赛事动态：国际体育赛事精彩纷呈，运动员表现亮眼"
        ]
        
        news_items = []
        for i, topic in enumerate(hot_topics[:NEWS_COUNT_PER_FETCH]):
            news_item = NewsItem(
                title=f"热点新闻 {i+1}",
                content=topic,
                source="热点聚合",
                url="",
                pub_date=datetime.now().strftime("%Y-%m-%d %H:%M")
            )
            news_items.append(news_item)
        
        return news_items
    
    def fetch_all_sources(self) -> List[NewsItem]:
        """从所有配置的源抓取新闻"""
        all_news = []
        
        # 从RSS源抓取
        for source in NEWS_SOURCES:
            if source.endswith('.rss') or 'rss' in source:
                items = self.fetch_from_rss(source)
                all_news.extend(items)
        
        # 从Google News抓取
        google_news = self.fetch_from_google_news("热点")
        all_news.extend(google_news)
        
        # 如果新闻数量不足，使用备用数据
        if len(all_news) < 5:
            logger.warning("新闻数量不足，使用备用数据源")
            backup_news = self.fetch_from_baidu_hot()
            all_news.extend(backup_news)
        
        # 去重
        seen_ids = set()
        unique_news = []
        for item in all_news:
            if item.id not in seen_ids:
                seen_ids.add(item.id)
                unique_news.append(item)
        
        # 更新缓存
        self.cached_news = unique_news[:NEWS_COUNT_PER_FETCH * 2]
        self._save_cache()
        
        return self.cached_news
    
    def get_cached_news(self) -> List[NewsItem]:
        """获取缓存的新闻"""
        if not self.cached_news:
            return self.fetch_all_sources()
        return self.cached_news
    
    def add_custom_news(self, title: str, content: str, source: str = "自定义") -> NewsItem:
        """添加自定义新闻"""
        news_item = NewsItem(
            title=title,
            content=content,
            source=source,
            url="",
            pub_date=datetime.now().strftime("%Y-%m-%d %H:%M")
        )
        self.cached_news.insert(0, news_item)
        self._save_cache()
        return news_item


# 用于API调用的异步新闻抓取（使用z-ai-web-dev-sdk）
class AsyncNewsFetcher:
    """异步新闻抓取器 - 使用AI API进行新闻搜索"""
    
    def __init__(self):
        # 这里可以集成z-ai-web-dev-sdk的web_search功能
        pass
    
    async def search_news_via_api(self, query: str, num: int = 10) -> List[NewsItem]:
        """通过API搜索新闻（需要在Node.js环境中运行）"""
        # 这个方法需要在Node.js环境中使用z-ai-web-dev-sdk
        # Python版本使用requests进行搜索
        pass


if __name__ == "__main__":
    # 测试新闻抓取
    fetcher = NewsFetcher()
    news = fetcher.fetch_all_sources()
    print(f"\n共抓取 {len(news)} 条新闻：")
    for i, item in enumerate(news[:5], 1):
        print(f"\n{i}. {item.title}")
        print(f"   来源: {item.source}")
        print(f"   内容: {item.content[:100]}...")

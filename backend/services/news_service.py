"""
News Service - News fetching and parsing
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
import feedparser
import httpx

from core.config import get_settings
from core.logger import get_logger

logger = get_logger("news")


@dataclass
class NewsItem:
    """Single news item"""
    title: str
    content: str
    source: str
    url: str
    published: Optional[datetime] = None
    hash: str = ""
    
    def __post_init__(self):
        if not self.hash:
            self.hash = hashlib.md5(f"{self.title}{self.source}".encode()).hexdigest()[:8]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content,
            "source": self.source,
            "url": self.url,
            "published": self.published.isoformat() if self.published else None,
            "hash": self.hash,
        }


class NewsService:
    """News fetching and parsing service"""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.settings = get_settings()
        self.cache_dir = cache_dir or self.settings.ASSETS_DIR / "news"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache_file = self.cache_dir / "news_cache.json"
        self._cache: Dict[str, NewsItem] = {}
        self._load_cache()
        
        logger.info(f"News Service initialized: cache={self.cache_file}")

    def _load_cache(self):
        """Load cached news"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._cache = {
                    h: NewsItem(**item) 
                    for h, item in data.items()
                }
                logger.debug(f"Loaded {len(self._cache)} cached news items")
            except Exception as e:
                logger.warning(f"Failed to load news cache: {e}")

    def _save_cache(self):
        """Save news cache"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    h: item.to_dict() 
                    for h, item in self._cache.items()
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save news cache: {e}")

    async def fetch_from_rss(
        self, 
        feed_url: str,
        max_items: int = 10
    ) -> List[NewsItem]:
        """
        Fetch news from RSS feed
        
        Args:
            feed_url: RSS feed URL
            max_items: Maximum items to fetch
            
        Returns:
            List of NewsItem
        """
        items = []
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(feed_url)
                response.raise_for_status()
            
            feed = feedparser.parse(response.text)
            
            for entry in feed.entries[:max_items]:
                # Parse published date
                published = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        published = datetime(*entry.published_parsed[:6])
                    except Exception:
                        pass
                
                item = NewsItem(
                    title=entry.get('title', 'No title'),
                    content=entry.get('summary', entry.get('description', '')),
                    source=feed.feed.get('title', feed_url),
                    url=entry.get('link', ''),
                    published=published,
                )
                
                # Add to cache if new
                if item.hash not in self._cache:
                    self._cache[item.hash] = item
                    items.append(item)
                else:
                    # Still add to results even if cached
                    items.append(self._cache[item.hash])
            
            logger.info(f"Fetched {len(items)} items from {feed_url}")
            
        except Exception as e:
            logger.error(f"Failed to fetch from {feed_url}: {e}")
        
        return items

    async def fetch_all(self, max_per_source: int = 5) -> List[NewsItem]:
        """Fetch from all configured sources"""
        all_items = []
        
        for source in self.settings.NEWS_SOURCES:
            items = await self.fetch_from_rss(source, max_per_source)
            all_items.extend(items)
        
        # Sort by published date (newest first)
        all_items.sort(
            key=lambda x: x.published or datetime.min,
            reverse=True
        )
        
        self._save_cache()
        return all_items

    def get_cached(self) -> List[NewsItem]:
        """Get all cached news items"""
        return list(self._cache.values())

    def get_item(self, hash: str) -> Optional[NewsItem]:
        """Get specific news item by hash"""
        return self._cache.get(hash)

    def format_for_tts(self, item: NewsItem, template: str = None) -> str:
        """
        Format news item for TTS
        
        Args:
            item: News item
            template: Optional format template
            
        Returns:
            Formatted text for TTS
        """
        template = template or "{title}。{content}"
        
        # Clean HTML tags
        import re
        content = re.sub(r'<[^>]+>', '', item.content)
        content = re.sub(r'\s+', ' ', content).strip()
        
        # Limit length
        if len(content) > 500:
            content = content[:500] + "..."
        
        return template.format(title=item.title, content=content)

    def add_custom(self, title: str, content: str) -> NewsItem:
        """Add custom news item"""
        item = NewsItem(
            title=title,
            content=content,
            source="custom",
            url="",
        )
        self._cache[item.hash] = item
        self._save_cache()
        return item

    def remove(self, hash: str) -> bool:
        """Remove news item from cache"""
        if hash in self._cache:
            del self._cache[hash]
            self._save_cache()
            return True
        return False

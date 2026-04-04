"""
api/routers/news.py — RSS news feed endpoint.

Fetches and caches sports news from public RSS feeds.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from fastapi import APIRouter, Request

from api.cache import TTLCache
from api.response_models import NewsResponse
from src.constants import CACHE_TTL_NEWS

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

router = APIRouter(prefix="/api", tags=["News"])

# ─── News RSS Cache ─────────────────────────────────────────────

_news_cache = TTLCache(ttl=CACHE_TTL_NEWS, name="news")

RSS_FEEDS = [
    {"url": "https://www.lequipe.fr/rss/actu_rss.xml", "source": "L'Équipe"},
    {"url": "https://rmcsport.bfmtv.com/rss/football/", "source": "RMC Sport"},
    {"url": "https://www.nhl.com/rss/news.xml", "source": "NHL.com"},
]


def _fetch_rss_news() -> list:
    """Fetch and parse RSS feeds, return list of news items."""
    if not HTTPX_AVAILABLE:
        return []
    items = []
    for feed in RSS_FEEDS:
        try:
            resp = httpx.get(feed["url"], timeout=5.0, follow_redirects=True)
            root = ET.fromstring(resp.text)
            channel = root.find("channel")
            if channel is None:
                continue
            for item in channel.findall("item")[:3]:
                title = item.findtext("title", "").strip()
                link = item.findtext("link", "").strip()
                pub_date = item.findtext("pubDate", "").strip()
                if title and link:
                    items.append(
                        {
                            "title": title,
                            "link": link,
                            "source": feed["source"],
                            "pub_date": pub_date,
                        }
                    )
        except Exception:
            pass
    return items[:6]


@router.get("/news", summary="Get latest sports news", response_model=NewsResponse)
def get_news(request: Request):
    """Get latest sports news from RSS feeds (cached 1h)."""
    data = _news_cache.get_or_set("news", _fetch_rss_news)
    return {"news": data}

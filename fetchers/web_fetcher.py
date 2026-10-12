"""
Web / RSS fetcher — pulls articles from major news outlets and newsletters.
No API key or account required. Uses public RSS feeds.

Scoring formula (no engagement metrics available from RSS):
  score = tier_weight + recency_bonus
  - tier_weight : Tier 1 = 30 pts, Tier 2 = 20 pts, Tier 3 = 10 pts
  - recency_bonus: last 24h = 30, last 48h = 20, last week = 10
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta

import feedparser

logger = logging.getLogger(__name__)


@dataclass
class Article:
    id: str
    source: str          # outlet name, e.g. "CoinDesk"
    author: str
    title: str
    summary: str         # short excerpt from the feed
    url: str
    published_at: datetime
    topic: str           # "AI & Machine Learning" | "Crypto & Blockchain"
    score: float         # computed authority + recency score
    extra: dict = field(default_factory=dict)


TIER_WEIGHTS = {1: 30, 2: 20, 3: 10}


class WebFetcher:
    def __init__(self, max_days_back: int = 7):
        self.max_days_back = max_days_back
        self.cutoff = datetime.now(timezone.utc) - timedelta(days=max_days_back)

    def fetch_top_articles(
        self,
        sources: dict[str, list[dict]],
        top_n: int = 10,
    ) -> list[Article]:
        """
        Fetch and rank articles from all RSS sources.

        Args:
            sources: dict mapping topic → list of {name, url, tier}
            top_n:   number of articles to return

        Returns:
            Top-N articles sorted by score descending
        """
        all_articles: list[Article] = []

        for topic, feed_list in sources.items():
            for feed_cfg in feed_list:
                try:
                    articles = self._parse_feed(feed_cfg, topic)
                    all_articles.extend(articles)
                    logger.info(
                        f"[RSS] {feed_cfg['name']} ({topic}) → {len(articles)} articles"
                    )
                except Exception as e:
                    logger.warning(f"[RSS] {feed_cfg['name']}: failed — {e}")

        # Deduplicate by URL
        seen_urls: set[str] = set()
        deduped: list[Article] = []
        for a in all_articles:
            if a.url not in seen_urls:
                seen_urls.add(a.url)
                deduped.append(a)

        # Sort by score (tier + recency)
        deduped.sort(key=lambda a: a.score, reverse=True)

        logger.info(
            f"[RSS] Total unique articles: {len(deduped)} — keeping top {top_n}"
        )
        return deduped[:top_n]

    def _parse_feed(self, feed_cfg: dict, topic: str) -> list[Article]:
        feed = feedparser.parse(feed_cfg["url"])
        tier = feed_cfg.get("tier", 2)
        tier_weight = TIER_WEIGHTS.get(tier, 10)
        articles = []

        for entry in feed.entries:
            published_at = self._parse_date(entry)
            if published_at is None or published_at < self.cutoff:
                continue

            # Recency bonus
            age_hours = (datetime.now(timezone.utc) - published_at).total_seconds() / 3600
            if age_hours <= 24:
                recency_bonus = 30
            elif age_hours <= 48:
                recency_bonus = 20
            else:
                recency_bonus = 10

            score = tier_weight + recency_bonus

            # Clean summary
            raw_summary = getattr(entry, "summary", "") or ""
            clean_summary = self._strip_html(raw_summary)[:400]

            # Author
            author = getattr(entry, "author", feed_cfg["name"])

            articles.append(
                Article(
                    id=getattr(entry, "id", entry.link),
                    source=feed_cfg["name"],
                    author=author,
                    title=getattr(entry, "title", "Untitled"),
                    summary=clean_summary,
                    url=getattr(entry, "link", ""),
                    published_at=published_at,
                    topic=topic,
                    score=score,
                    extra={"tier": tier},
                )
            )

        return articles

    @staticmethod
    def _parse_date(entry) -> datetime | None:
        """Try multiple date fields and return a timezone-aware datetime."""
        for attr in ("published_parsed", "updated_parsed", "created_parsed"):
            t = getattr(entry, attr, None)
            if t:
                try:
                    dt = datetime(*t[:6], tzinfo=timezone.utc)
                    return dt
                except Exception:
                    continue
        return None

    @staticmethod
    def _strip_html(text: str) -> str:
        """Remove HTML tags from a string."""
        import re
        clean = re.sub(r"<[^>]+>", "", text)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

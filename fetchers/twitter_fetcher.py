"""
Twitter / X fetcher — uses Twitter API v2 via tweepy.

Requirements:
  - Twitter Developer account with at least the Basic tier ($100/mo)
    to search and read tweets from other accounts.
  - Set TWITTER_BEARER_TOKEN in your .env file.
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field

import tweepy

logger = logging.getLogger(__name__)


@dataclass
class Post:
    id: str
    source: str          # "twitter"
    author: str          # @handle
    content: str
    likes: int
    url: str
    created_at: datetime
    topic_group: str     # "ai_official", "crypto_influencers", etc.
    extra: dict = field(default_factory=dict)


class TwitterFetcher:
    def __init__(self):
        bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        if not bearer_token:
            raise ValueError("TWITTER_BEARER_TOKEN is not set in environment.")
        self.client = tweepy.Client(bearer_token=bearer_token, wait_on_rate_limit=True)

    def fetch_top_posts(
        self,
        accounts: dict[str, list[str]],
        top_n: int = 10,
        hours_back: int = 24,
    ) -> list[Post]:
        """
        Fetch the most-liked tweets from a dict of {group: [handles]}.
        Returns a flat list of Post objects sorted by likes descending.
        """
        all_posts: list[Post] = []
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)

        for group, handles in accounts.items():
            for handle in handles:
                try:
                    posts = self._fetch_user_tweets(handle, group, start_time)
                    all_posts.extend(posts)
                    logger.info(f"[Twitter] @{handle} → {len(posts)} tweets fetched")
                except tweepy.errors.Forbidden as e:
                    logger.warning(
                        f"[Twitter] @{handle}: access denied — "
                        "your API tier may not support reading other users' tweets. "
                        f"Details: {e}"
                    )
                except tweepy.errors.NotFound:
                    logger.warning(f"[Twitter] @{handle}: account not found, skipping.")
                except Exception as e:
                    logger.error(f"[Twitter] @{handle}: unexpected error — {e}")

        all_posts.sort(key=lambda p: p.likes, reverse=True)
        return all_posts[:top_n]

    def _fetch_user_tweets(
        self, handle: str, group: str, start_time: datetime
    ) -> list[Post]:
        user_resp = self.client.get_user(username=handle, user_fields=["id"])
        if not user_resp.data:
            return []

        user_id = user_resp.data.id
        resp = self.client.get_users_tweets(
            id=user_id,
            start_time=start_time,
            max_results=100,
            tweet_fields=["created_at", "public_metrics", "text"],
            exclude=["retweets", "replies"],
        )

        posts = []
        if resp.data:
            for tweet in resp.data:
                metrics = tweet.public_metrics or {}
                likes = metrics.get("like_count", 0)
                posts.append(
                    Post(
                        id=str(tweet.id),
                        source="twitter",
                        author=f"@{handle}",
                        content=tweet.text,
                        likes=likes,
                        url=f"https://twitter.com/{handle}/status/{tweet.id}",
                        created_at=tweet.created_at or start_time,
                        topic_group=group,
                    )
                )
        return posts

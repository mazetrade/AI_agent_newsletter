"""
Reddit fetcher — uses PRAW (Python Reddit API Wrapper).

Requirements:
  - Create a Reddit app at https://www.reddit.com/prefs/apps (free)
  - Set REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT in your .env
"""

import os
import logging
from datetime import datetime, timezone, timedelta

import praw

from fetchers.twitter_fetcher import Post  # reuse the same Post dataclass

logger = logging.getLogger(__name__)


class RedditFetcher:
    def __init__(self):
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        user_agent = os.getenv("REDDIT_USER_AGENT", "AI-Crypto-Newsletter/1.0")

        if not client_id or not client_secret:
            raise ValueError(
                "REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET must be set in environment."
            )

        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )

    def fetch_top_posts(
        self,
        subreddits: dict[str, list[str]],
        top_n: int = 10,
        hours_back: int = 24,
    ) -> list[Post]:
        """
        Fetch the most-liked posts from a dict of {group: [subreddit_names]}.
        Returns a flat list sorted by upvotes descending.
        """
        all_posts: list[Post] = []
        cutoff_ts = (
            datetime.now(timezone.utc) - timedelta(hours=hours_back)
        ).timestamp()

        for group, subreddit_names in subreddits.items():
            for name in subreddit_names:
                try:
                    posts = self._fetch_subreddit_posts(name, group, cutoff_ts)
                    all_posts.extend(posts)
                    logger.info(f"[Reddit] r/{name} → {len(posts)} posts fetched")
                except Exception as e:
                    logger.error(f"[Reddit] r/{name}: error — {e}")

        all_posts.sort(key=lambda p: p.likes, reverse=True)
        return all_posts[:top_n]

    def _fetch_subreddit_posts(
        self, subreddit_name: str, group: str, cutoff_ts: float
    ) -> list[Post]:
        subreddit = self.reddit.subreddit(subreddit_name)
        posts = []

        # "hot" gives recently active + highly upvoted posts
        for submission in subreddit.hot(limit=50):
            if submission.created_utc < cutoff_ts:
                continue
            if submission.is_self and not submission.selftext:
                continue  # skip empty text posts

            content = submission.title
            if submission.selftext:
                # Include a short excerpt of the body
                body_preview = submission.selftext[:300].replace("\n", " ").strip()
                content = f"{submission.title} — {body_preview}"

            posts.append(
                Post(
                    id=submission.id,
                    source="reddit",
                    author=f"u/{submission.author.name if submission.author else 'deleted'}",
                    content=content,
                    likes=submission.score,
                    url=f"https://reddit.com{submission.permalink}",
                    created_at=datetime.fromtimestamp(
                        submission.created_utc, tz=timezone.utc
                    ),
                    topic_group=group,
                    extra={
                        "subreddit": subreddit_name,
                        "num_comments": submission.num_comments,
                        "upvote_ratio": submission.upvote_ratio,
                    },
                )
            )

        return posts

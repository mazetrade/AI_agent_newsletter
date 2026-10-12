"""
AI & Crypto Pulse — Newsletter Agent
=====================================
Pipeline:
  1. Fetch top articles from RSS feeds (major news outlets, no API needed)
  2. Rank by source authority + recency
  3. Summarize with Claude into a full newsletter
  4. Render HTML email
  5. Send via Gmail

Run:
    python main.py              # full run
    python main.py --save-html  # also save HTML to disk
    python main.py --dry-run    # build but do NOT send email
"""

import argparse
import logging
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

from config.sources import RSS_SOURCES, TOP_N, MAX_DAYS_BACK
from fetchers.web_fetcher import WebFetcher, Article
from agents.summarizer import NewsletterSummarizer
from newsletter.builder import NewsletterBuilder
from newsletter.sender import EmailSender

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI & Crypto Pulse Newsletter Agent")
    parser.add_argument("--save-html", action="store_true", help="Save HTML to disk")
    parser.add_argument("--dry-run", action="store_true", help="Build but do not send")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    now = datetime.now(timezone.utc)

    logger.info("╔══════════════════════════════════════════╗")
    logger.info("║   AI & Crypto Pulse — Newsletter Agent   ║")
    logger.info(f"║   Edition: {now.strftime('%B %d, %Y'):<30} ║")
    logger.info("╚══════════════════════════════════════════╝")

    # Step 1 — Fetch articles from RSS feeds
    logger.info("=== Fetching articles from RSS feeds ===")
    fetcher = WebFetcher(max_days_back=MAX_DAYS_BACK)
    articles: list[Article] = fetcher.fetch_top_articles(
        sources=RSS_SOURCES,
        top_n=TOP_N,
    )

    if not articles:
        logger.error("No articles fetched. Check your internet connection.")
        sys.exit(1)

    logger.info(f"=== Top {len(articles)} articles selected ===")
    for i, a in enumerate(articles, 1):
        logger.info(f"  #{i:02d}  [{a.source:<20}] {a.title[:60]}...")

    # Step 2 — Summarize with Claude
    logger.info("=== Summarizing with Claude ===")
    summarizer = NewsletterSummarizer()
    summary = summarizer.summarize(articles, date=now)

    # Step 3 — Build HTML newsletter
    logger.info("=== Building newsletter HTML ===")
    builder = NewsletterBuilder()
    html = builder.build(summary, date=now)

    if args.save_html:
        path = builder.save(html, date=now)
        logger.info(f"HTML saved → {path}")

    # Step 4 — Send email
    if args.dry_run:
        logger.info("=== DRY RUN — email not sent ===")
        if not args.save_html:
            logger.info("Tip: run with --save-html to inspect the output.")
    else:
        logger.info("=== Sending email ===")
        sender = EmailSender()
        sender.send(html, date=now)

    logger.info("=== Done! ===")


if __name__ == "__main__":
    main()

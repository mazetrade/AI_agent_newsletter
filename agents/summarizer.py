"""
Summarizer agent — uses Claude to turn raw articles into a polished newsletter.

Steps:
  1. Receives top articles ranked by score
  2. Asks Claude to write a full newsletter: intro + per-article paragraphs + closing
"""

import os
import logging
from datetime import datetime

import anthropic

from fetchers.web_fetcher import Article

logger = logging.getLogger(__name__)

MODEL = "claude-haiku-4-5-20251001"  # cheapest model — switch to claude-sonnet-4-6 for production


class NewsletterSummarizer:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set in environment.")
        self.client = anthropic.Anthropic(api_key=api_key)

    def summarize(self, articles: list[Article], date: datetime) -> dict:
        """
        Takes a ranked list of Article objects and returns a dict:
        {
            "intro": str,
            "items": [{"rank": int, "paragraph": str, "source": str,
                       "author": str, "url": str, "title": str,
                       "published_at": str, "topic": str}, ...],
            "closing": str,
        }
        """
        if not articles:
            return {"intro": "No articles found for this week.", "items": [], "closing": ""}

        articles_block = self._format_articles_for_prompt(articles)
        date_str = date.strftime("%B %d, %Y")

        prompt = f"""You are an expert tech and finance journalist writing a premium weekly newsletter.
Today is {date_str}.

Below are the top {len(articles)} most important articles from the past week, sourced from leading news outlets and newsletters covering AI, crypto, and blockchain.

{articles_block}

Your task:
1. Write a compelling **introduction paragraph** (3–4 sentences) that sets the scene for this week's edition and highlights the key themes across AI and crypto.

2. For each article (numbered 1 to {len(articles)}), write a **dedicated paragraph** (4–6 sentences) that:
   - Explains what the article is about in plain, engaging language
   - Gives context: why this matters, what it means for the industry or readers
   - Naturally weaves in the source name and author where relevant
   - Feels like journalism, not a summary

3. Write a **closing paragraph** (2–3 sentences) with a forward-looking thought about the week ahead.

Format your response EXACTLY as follows (use these exact delimiters):

[INTRO]
<introduction paragraph here>
[/INTRO]

[ITEM_1]
<paragraph for article 1>
[/ITEM_1]

[ITEM_2]
<paragraph for article 2>
[/ITEM_2]

... and so on up to [ITEM_{len(articles)}]

[CLOSING]
<closing paragraph here>
[/CLOSING]

Write in a professional but engaging tone. No bullet points — only flowing prose paragraphs."""

        logger.info("[Summarizer] Calling Claude API...")
        message = self.client.messages.create(
            model=MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        raw_text = message.content[0].text
        return self._parse_response(raw_text, articles)

    def _format_articles_for_prompt(self, articles: list[Article]) -> str:
        lines = []
        for i, a in enumerate(articles, 1):
            lines.append(
                f"ARTICLE {i}:\n"
                f"  Topic:       {a.topic}\n"
                f"  Source:      {a.source}\n"
                f"  Author:      {a.author}\n"
                f"  Published:   {a.published_at.strftime('%B %d, %Y at %H:%M UTC')}\n"
                f"  Title:       {a.title}\n"
                f"  Summary:     {a.summary}\n"
                f"  URL:         {a.url}\n"
            )
        return "\n".join(lines)

    def _parse_response(self, raw: str, articles: list[Article]) -> dict:
        def extract(tag: str) -> str:
            start = raw.find(f"[{tag}]")
            end = raw.find(f"[/{tag}]")
            if start == -1 or end == -1:
                return ""
            return raw[start + len(f"[{tag}]"):end].strip()

        intro = extract("INTRO")
        closing = extract("CLOSING")

        items = []
        for i, article in enumerate(articles, 1):
            paragraph = extract(f"ITEM_{i}")
            items.append(
                {
                    "rank": i,
                    "paragraph": paragraph,
                    "source": article.source,
                    "author": article.author,
                    "url": article.url,
                    "title": article.title,
                    "published_at": article.published_at.strftime("%b %d, %Y"),
                    "topic": article.topic,
                    "summary_preview": article.summary[:120] + "..."
                    if len(article.summary) > 120
                    else article.summary,
                }
            )

        return {"intro": intro, "items": items, "closing": closing}

"""
Newsletter builder — renders the Jinja2 HTML template with summarized content.
"""

import os
import logging
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class NewsletterBuilder:
    def __init__(self):
        self.env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

    def build(self, summary: dict, date: datetime) -> str:
        """
        Renders the HTML newsletter from the summary dict returned by the summarizer.

        Args:
            summary: {"intro": str, "items": [...], "closing": str}
            date: the edition date

        Returns:
            Rendered HTML string
        """
        template = self.env.get_template("newsletter.html")

        # Sort items so AI topics come before Crypto (consistent ordering)
        items = sorted(
            summary.get("items", []),
            key=lambda x: (0 if "AI" in x.get("topic", "") else 1, x["rank"]),
        )

        html = template.render(
            edition_title=f"AI & Crypto Pulse — {date.strftime('%B %d, %Y')}",
            date=date.strftime("%A, %B %d, %Y"),
            intro=summary.get("intro", ""),
            items=items,
            closing=summary.get("closing", ""),
        )

        logger.info("[Builder] Newsletter HTML rendered successfully.")
        return html

    def save(self, html: str, date: datetime, output_dir: str = ".") -> str:
        """Optionally save the HTML to disk for inspection."""
        filename = f"newsletter_{date.strftime('%Y-%m-%d')}.html"
        path = os.path.join(output_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info(f"[Builder] Newsletter saved to {path}")
        return path

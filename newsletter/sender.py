"""
Email sender — sends the HTML newsletter via SMTP.

Supports Gmail (default) and any other SMTP provider.

Gmail setup:
  1. Enable 2-step verification on your Google account
  2. Go to https://myaccount.google.com/apppasswords
  3. Generate an App Password for "Mail"
  4. Use that password as EMAIL_PASSWORD in your .env
"""

import os
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailSender:
    def __init__(self):
        self.sender = os.getenv("EMAIL_SENDER")
        self.password = os.getenv("EMAIL_PASSWORD")
        self.recipients_raw = os.getenv("EMAIL_RECIPIENTS", "")
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))

        if not self.sender or not self.password:
            raise ValueError(
                "EMAIL_SENDER and EMAIL_PASSWORD must be set in environment."
            )
        if not self.recipients_raw:
            raise ValueError("EMAIL_RECIPIENTS must be set (comma-separated emails).")

        self.recipients = [r.strip() for r in self.recipients_raw.split(",") if r.strip()]

    def send(self, html: str, date: datetime) -> None:
        """
        Sends the HTML newsletter to all configured recipients.

        Args:
            html: Rendered HTML content
            date: Edition date (used in subject line)
        """
        subject = f"AI & Crypto Pulse — {date.strftime('%B %d, %Y')}"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = ", ".join(self.recipients)

        # Attach both a plain-text fallback and the HTML version
        plain_text = (
            f"AI & Crypto Pulse Newsletter\n"
            f"Edition: {date.strftime('%B %d, %Y')}\n\n"
            "Please view this email in an HTML-compatible client for the best experience."
        )
        msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(html, "html"))

        logger.info(f"[Sender] Connecting to {self.smtp_host}:{self.smtp_port}...")

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(self.sender, self.password)
            server.sendmail(self.sender, self.recipients, msg.as_string())

        logger.info(
            f"[Sender] Newsletter sent to {len(self.recipients)} recipient(s): "
            f"{', '.join(self.recipients)}"
        )

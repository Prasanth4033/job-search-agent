"""
Email notifier — sends the HTML report via Gmail SMTP.
Uses App Password authentication (no OAuth required).
"""

from __future__ import annotations

import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from ..scrapers.base import JobPosting
from ..notifiers.html_reporter import build_html_report
from ..utils.logger import logger


class EmailNotifier:
    """
    Sends the daily job report as an HTML email via Gmail SMTP.

    Prerequisites:
      1. Enable 2-Step Verification on your Google account.
      2. Generate an App Password at https://myaccount.google.com/apppasswords
      3. Set EMAIL_SENDER and EMAIL_PASSWORD in your .env file.
    """

    def __init__(self, cfg: dict):
        email_cfg         = cfg.get("email", {})
        self.smtp_host    = email_cfg.get("smtp_host", "smtp.gmail.com")
        self.smtp_port    = int(email_cfg.get("smtp_port", 587))
        self.sender       = email_cfg.get("sender", "")
        self.password     = email_cfg.get("password", "")
        self.recipient    = email_cfg.get("recipient", "")

        if not all([self.sender, self.password, self.recipient]):
            raise ValueError(
                "Email configuration incomplete. "
                "Set EMAIL_SENDER, EMAIL_PASSWORD, and EMAIL_RECIPIENT in .env"
            )

    def _build_message(
        self,
        postings: List[JobPosting],
        run_date: datetime,
    ) -> MIMEMultipart:
        count   = len(postings)
        subject = (
            f"🔔 Daily DE Jobs — {run_date.strftime('%b %d, %Y')} "
            f"| {count} New Posting{'s' if count != 1 else ''}"
        )

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"Job Search Agent <{self.sender}>"
        msg["To"]      = self.recipient

        # Plain-text fallback
        plain_lines = [
            f"Daily Data Engineering Job Report — {run_date.strftime('%B %d, %Y')}",
            f"{count} new posting(s) found.\n",
        ]
        for p in postings:
            plain_lines.append(
                f"• {p.title} | {p.location} | {p.source}\n  {p.apply_url}"
            )
        plain_text = "\n".join(plain_lines)

        # HTML body
        html_body = build_html_report(postings, run_date)

        msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(html_body, "html"))
        return msg

    def send(self, postings: List[JobPosting], run_date: datetime) -> bool:
        """Send the report email. Returns True on success."""
        try:
            msg = self._build_message(postings, run_date)
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(self.sender, self.password)
                server.sendmail(self.sender, [self.recipient], msg.as_string())
            logger.info(f"Email sent to {self.recipient} — {len(postings)} postings.")
            return True
        except smtplib.SMTPAuthenticationError:
            logger.error(
                "Gmail authentication failed. "
                "Ensure EMAIL_PASSWORD is a valid App Password "
                "(https://myaccount.google.com/apppasswords)."
            )
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
        except Exception as e:
            logger.error(f"Unexpected email error: {e}")
        return False

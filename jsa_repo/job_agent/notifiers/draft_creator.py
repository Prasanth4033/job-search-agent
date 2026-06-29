"""
Gmail Draft Creator — v2.
Creates a per-job Gmail draft with:
  - Subject: Application for <job title> at <company>
  - Body: Professional cover note with SPOC details + matched skills list
  - Attachment: Tailored ATS .docx resume

Two backends supported:
  1. Gmail API (OAuth2) — preferred, supports attachments in drafts
  2. SMTP fallback — saves email as .eml file if Gmail API unavailable

Gmail API setup:
  - Enable Gmail API in Google Cloud Console
  - Create OAuth2 credentials (Desktop app type)
  - Download credentials.json to the project root
  - First run will open browser for auth and save token.json
"""

from __future__ import annotations

import base64
import json
import os
import re
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from ..scrapers.base import JobPosting
from ..utils.logger import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TOKEN_FILE       = PROJECT_ROOT / "token.json"
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
SENDER_EMAIL     = os.getenv("EMAIL_SENDER", "gspr4033@gmail.com")


# ──────────────────────────────────────────────
# Email body builder
# ──────────────────────────────────────────────

def _build_body(job: JobPosting) -> str:
    spoc_line = ""
    if job.spoc_name or job.spoc_email:
        parts = []
        if job.spoc_name:
            parts.append(f"Hiring Manager / Recruiter: {job.spoc_name}")
        if job.spoc_email:
            parts.append(f"Contact: {job.spoc_email}")
        if job.spoc_phone:
            parts.append(f"Phone: {job.spoc_phone}")
        spoc_line = "\n".join(parts) + "\n\n"

    skills_block = ""
    if job.matched_skills:
        skills_block = (
            "Key skills from my profile that match this role:\n"
            + ", ".join(job.matched_skills[:15])
            + "\n\n"
        )

    body = (
        f"Dear {job.spoc_name or 'Hiring Manager'},\n\n"
        f"I am writing to express my strong interest in the {job.title} position at {job.company}.\n\n"
        f"With 11+ years of experience as a Senior Data Engineer specialising in AWS, GCP, "
        f"Databricks, and Snowflake, I am confident I can add immediate value to your team.\n\n"
        f"{skills_block}"
        f"I have attached my tailored resume for your review. I would welcome the opportunity "
        f"to discuss how my background aligns with your needs.\n\n"
        f"Job Reference: {job.apply_url}\n"
        f"Posted: {job.posted_date.strftime('%Y-%m-%d') if job.posted_date else 'Recently'}\n"
        f"Source: {job.source}\n\n"
        f"{spoc_line}"
        f"Thank you for your time and consideration.\n\n"
        f"Best regards,\n"
        f"Sai Prasanth Gudibandla\n"
        f"gspr4033@gmail.com\n"
        f"+1 (636) 431-6758\n"
        f"linkedin.com/in/sai-prasanth-gudibandla"
    )
    return body


def _build_subject(job: JobPosting) -> str:
    return f"Application for {job.title} at {job.company}"


# ──────────────────────────────────────────────
# Gmail API backend
# ──────────────────────────────────────────────

def _build_mime_message(job: JobPosting, resume_path: Optional[Path]) -> MIMEMultipart:
    msg = MIMEMultipart()
    msg["To"]      = SENDER_EMAIL     # drafts go to self; user edits To before sending
    msg["From"]    = SENDER_EMAIL
    msg["Subject"] = _build_subject(job)

    # Plain text body
    msg.attach(MIMEText(_build_body(job), "plain"))

    # Attach resume .docx
    if resume_path and Path(resume_path).exists():
        with open(resume_path, "rb") as f:
            part = MIMEApplication(f.read(), Name=Path(resume_path).name)
        part["Content-Disposition"] = f'attachment; filename="{Path(resume_path).name}"'
        msg.attach(part)
    else:
        logger.warning(f"[DraftCreator] Resume not found at {resume_path} — skipping attachment.")

    return msg


def _get_gmail_service():
    """Return an authenticated Gmail API service object."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        logger.error("[DraftCreator] google-api-python-client not installed. Run: pip install google-api-python-client google-auth-oauthlib")
        return None

    SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]
    creds  = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.warning(f"[DraftCreator] Token refresh failed: {e}")
                creds = None
        if not creds:
            if not CREDENTIALS_FILE.exists():
                logger.error(
                    f"[DraftCreator] credentials.json not found at {CREDENTIALS_FILE}. "
                    "Download from Google Cloud Console and place in the project root."
                )
                return None
            flow  = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        # Save token for next run
        with open(TOKEN_FILE, "w") as tf:
            tf.write(creds.to_json())

    try:
        from googleapiclient.discovery import build
        return build("gmail", "v1", credentials=creds)
    except Exception as e:
        logger.error(f"[DraftCreator] Failed to build Gmail service: {e}")
        return None


def create_draft_gmail_api(job: JobPosting, resume_path: Optional[Path] = None) -> bool:
    """
    Create a Gmail draft via Gmail API.
    Returns True on success, False on failure.
    """
    service = _get_gmail_service()
    if service is None:
        return False

    mime_msg = _build_mime_message(job, resume_path)
    raw      = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode("utf-8")
    body     = {"message": {"raw": raw}}

    try:
        draft = service.users().drafts().create(userId="me", body=body).execute()
        logger.info(f"[DraftCreator] Draft created: {draft.get('id')} — {job.title} @ {job.company}")
        return True
    except Exception as e:
        logger.error(f"[DraftCreator] Gmail API draft creation failed: {e}")
        return False


# ──────────────────────────────────────────────
# EML fallback (no Gmail API)
# ──────────────────────────────────────────────

EML_DIR = PROJECT_ROOT / "drafts"

def create_draft_eml_fallback(job: JobPosting, resume_path: Optional[Path] = None) -> Path:
    """
    Save draft as .eml file when Gmail API is unavailable.
    Double-click the .eml file to open in Gmail/Outlook.
    """
    EML_DIR.mkdir(exist_ok=True)
    mime_msg = _build_mime_message(job, resume_path)

    safe_company = re.sub(r"[^A-Za-z0-9]+", "_", job.company)[:20]
    safe_title   = re.sub(r"[^A-Za-z0-9]+", "_", job.title)[:30]
    filename     = f"draft_{safe_title}_{safe_company}.eml"
    out_path     = EML_DIR / filename

    with open(out_path, "wb") as f:
        f.write(mime_msg.as_bytes())

    logger.info(f"[DraftCreator] EML saved: {out_path}")
    return out_path


# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────

def create_draft(job: JobPosting, resume_path: Optional[Path] = None) -> bool:
    """
    Attempt to create a Gmail draft for the given job.
    Falls back to saving an .eml file if Gmail API is unavailable.

    Returns True if Gmail API draft was created, False otherwise
    (fallback .eml is still created on False).
    """
    success = create_draft_gmail_api(job, resume_path)
    if not success:
        logger.warning(f"[DraftCreator] Gmail API unavailable — saving .eml fallback for {job.title}")
        create_draft_eml_fallback(job, resume_path)
    return success

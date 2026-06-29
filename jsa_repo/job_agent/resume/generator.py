"""
ATS-optimised resume generator — v2.
Generates a tailored .docx resume for each job posting using python-docx.
Rules:
  - No special characters (bullets use plain hyphens, no Unicode bullets/dashes)
  - Plain ASCII only in text runs
  - Fonts: Calibri 11pt body, 14pt name, 12pt section headers
  - Keywords from the job description injected into summary and skills
  - Skills section reordered: most-matching categories first
  - No tables, no text boxes (ATS-unfriendly)
"""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from .candidate_profile import CANDIDATE, ALL_SKILLS_FLAT
from ..utils.logger import logger


# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────

RESUME_DIR = Path(__file__).resolve().parent.parent.parent / "resumes"
RESUME_DIR.mkdir(exist_ok=True)

FONT_NAME  = "Calibri"
NAME_SIZE  = 14
HEAD_SIZE  = 12
BODY_SIZE  = 11


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _clean(text: str) -> str:
    """Remove non-ASCII and problematic Unicode characters for ATS safety."""
    # Normalise to ASCII where possible
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    # Replace curly quotes, em/en dashes
    text = text.replace("–", "-").replace("—", "-")
    text = text.replace("‘", "'").replace("’", "'")
    text = text.replace("“", '"').replace("”", '"')
    return text.strip()


def _set_font(run, size: int, bold: bool = False, color: Optional[RGBColor] = None):
    run.font.name = FONT_NAME
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = color


def _add_heading(doc: Document, text: str):
    """Add a styled section heading with a bottom border line."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after  = Pt(2)
    run = p.add_run(_clean(text.upper()))
    _set_font(run, HEAD_SIZE, bold=True, color=RGBColor(0x1F, 0x49, 0x7D))
    # Horizontal rule via paragraph bottom border
    pPr  = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"),   "single")
    bottom.set(qn("w:sz"),    "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "1F497D")
    pBdr.append(bottom)
    pPr.append(pBdr)
    return p


def _add_bullet(doc: Document, text: str, indent: float = 0.25):
    """Add a plain-text bullet (hyphen prefix, no Unicode)."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent    = Pt(indent * 72)
    p.paragraph_format.first_line_indent = Pt(-12)
    p.paragraph_format.space_after   = Pt(1)
    run = p.add_run(f"- {_clean(text)}")
    _set_font(run, BODY_SIZE)
    return p


def _add_body(doc: Document, text: str):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(_clean(text))
    _set_font(run, BODY_SIZE)
    return p


# ──────────────────────────────────────────────
# Skill matching
# ──────────────────────────────────────────────

def _extract_keywords(jd_text: str) -> List[str]:
    """Return unique lowercased words from the JD (3+ chars)."""
    words = re.findall(r"[A-Za-z][A-Za-z0-9+#./-]{2,}", jd_text)
    return list({w.lower() for w in words})


def match_skills(jd_text: str) -> Tuple[List[str], Dict[str, List[str]]]:
    """
    Returns:
      matched_flat  — flat list of matched skill names (for JobPosting.matched_skills)
      ordered_cats  — {category: [matched skills]} sorted by match count desc
    """
    jd_lower = jd_text.lower()
    matched_flat: List[str]  = []
    cat_matches: Dict[str, List[str]] = {}

    for cat, skills in CANDIDATE["skills"].items():
        hits = [s for s in skills if s.lower() in jd_lower or
                any(word in jd_lower for word in s.lower().split())]
        if hits:
            cat_matches[cat] = hits
            matched_flat.extend(hits)

    # Sort categories by number of matches
    ordered = dict(sorted(cat_matches.items(), key=lambda x: -len(x[1])))
    return matched_flat, ordered


def _build_summary(top_skills: List[str]) -> str:
    skill_str = ", ".join(top_skills[:5]) if top_skills else "AWS, GCP, Databricks, Snowflake, PySpark"
    tmpl = CANDIDATE["summary_template"]
    return tmpl.format(top_skills=skill_str)


# ──────────────────────────────────────────────
# Document builder
# ──────────────────────────────────────────────

def _build_document(job_title: str, company: str, jd_text: str) -> Document:
    doc = Document()

    # ── page margins (1 inch all sides) ──
    for section in doc.sections:
        section.top_margin    = Pt(72)
        section.bottom_margin = Pt(72)
        section.left_margin   = Pt(72)
        section.right_margin  = Pt(72)

    # ── name + contact ──
    name_p = doc.add_paragraph()
    name_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    name_p.paragraph_format.space_after = Pt(2)
    name_run = name_p.add_run(CANDIDATE["name"])
    _set_font(name_run, NAME_SIZE, bold=True)

    contact_p = doc.add_paragraph()
    contact_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    contact_p.paragraph_format.space_after = Pt(6)
    contact_text = (
        f"{CANDIDATE['email']}  |  {CANDIDATE['phone']}  |  "
        f"{CANDIDATE['linkedin']}  |  {CANDIDATE['location']}"
    )
    contact_run = contact_p.add_run(_clean(contact_text))
    _set_font(contact_run, BODY_SIZE)

    # ── skill matching ──
    matched_flat, ordered_cats = match_skills(jd_text)
    top_skills = matched_flat[:8] if matched_flat else list(CANDIDATE["skills"].get("Cloud - AWS", []))[:5]

    # ── summary ──
    _add_heading(doc, "Professional Summary")
    _add_body(doc, _build_summary(top_skills))

    # ── skills ──
    _add_heading(doc, "Technical Skills")
    # Show matched categories first, then remaining
    all_cats = list(ordered_cats.keys()) + [c for c in CANDIDATE["skills"] if c not in ordered_cats]
    for cat in all_cats:
        skills_in_cat = CANDIDATE["skills"].get(cat, [])
        if not skills_in_cat:
            continue
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(1)
        label_run = p.add_run(f"{cat}: ")
        _set_font(label_run, BODY_SIZE, bold=True)
        val_run = p.add_run(", ".join(_clean(s) for s in skills_in_cat))
        _set_font(val_run, BODY_SIZE)

    # ── experience ──
    _add_heading(doc, "Professional Experience")
    for exp in CANDIDATE["experience"]:
        # Role header
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after  = Pt(1)
        title_run = p.add_run(f"{exp['title']} - {exp['company']}")
        _set_font(title_run, BODY_SIZE, bold=True)

        # Location and dates
        meta_p = doc.add_paragraph()
        meta_p.paragraph_format.space_after = Pt(1)
        meta_run = meta_p.add_run(f"{exp['location']}  |  {exp['start']} - {exp['end']}")
        _set_font(meta_run, BODY_SIZE)

        # Bullets
        for bullet in exp["bullets"]:
            _add_bullet(doc, bullet)

    # ── education ──
    _add_heading(doc, "Education")
    for edu in CANDIDATE["education"]:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(1)
        r1 = p.add_run(f"{edu['degree']} - {edu['school']}")
        _set_font(r1, BODY_SIZE, bold=True)
        p2 = doc.add_paragraph()
        p2.paragraph_format.space_after = Pt(1)
        r2 = p2.add_run(f"Year: {edu['year']}")
        _set_font(r2, BODY_SIZE)

    # ── certifications ──
    _add_heading(doc, "Certifications")
    for cert in CANDIDATE["certifications"]:
        _add_bullet(doc, cert)

    return doc


# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────

def generate_resume(
    job_title: str,
    company: str,
    jd_text: str,
    output_dir: Optional[Path] = None,
) -> Tuple[Path, List[str]]:
    """
    Generate a tailored ATS resume .docx for the given job.

    Returns:
        (path_to_docx, matched_skills_list)
    """
    out_dir  = output_dir or RESUME_DIR
    out_dir  = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    matched_flat, _ = match_skills(jd_text)

    # Build filename safe for all OS
    safe_company = re.sub(r"[^A-Za-z0-9]+", "_", company)[:30]
    safe_title   = re.sub(r"[^A-Za-z0-9]+", "_", job_title)[:40]
    filename     = f"SaiPrasanth_{safe_title}_{safe_company}.docx"
    output_path  = out_dir / filename

    try:
        doc = _build_document(job_title, company, jd_text)
        doc.save(str(output_path))
        logger.info(f"[ResumeGenerator] Saved: {output_path}")
    except Exception as e:
        logger.error(f"[ResumeGenerator] Failed for {job_title} @ {company}: {e}")
        raise

    return output_path, matched_flat

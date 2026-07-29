from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from tools._shared import err
from tools.paper_text.tool import _download_arxiv_pdf


HEADING_PATTERNS = (
    re.compile(r"^\s*(\d+(?:\.\d+)*)[.)]?\s+([A-Z][^\n]{1,100})\s*$"),
    re.compile(
        r"^\s*(abstract|introduction|background|related work|method(?:ology)?|"
        r"approach|model|experiments?|experimental setup|evaluation|results?|"
        r"discussion|analysis|limitations?|conclusion|references|appendix)\s*$",
        re.IGNORECASE,
    ),
)


def _read_pages(pdf_path: Path) -> list[str]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("Install pypdf first: pip install pypdf") from exc

    reader = PdfReader(str(pdf_path))
    return [(page.extract_text() or "").strip() for page in reader.pages]


def _heading(line: str) -> str | None:
    candidate = " ".join(line.split())
    if not candidate or len(candidate) > 120:
        return None
    for pattern in HEADING_PATTERNS:
        match = pattern.match(candidate)
        if match:
            return candidate
    return None


def _structure_pages(pages: list[str]) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    current: dict[str, Any] = {"title": "Front matter", "start_page": 1, "end_page": 1, "parts": []}

    for page_number, page_text in enumerate(pages, start=1):
        for raw_line in page_text.splitlines():
            title = _heading(raw_line)
            if title:
                if current["parts"]:
                    current["text"] = "\n".join(current.pop("parts")).strip()
                    sections.append(current)
                current = {
                    "title": title,
                    "start_page": page_number,
                    "end_page": page_number,
                    "parts": [],
                }
            else:
                current["parts"].append(raw_line)
                current["end_page"] = page_number

    if current["parts"]:
        current["text"] = "\n".join(current.pop("parts")).strip()
        sections.append(current)
    return [section for section in sections if section.get("text")]


def read_structured_paper(arxiv_url: str = "", max_chars_per_section: int = 12000) -> dict[str, Any]:
    try:
        arxiv_id, pdf_path, pdf_url = _download_arxiv_pdf(arxiv_url)
        pages = _read_pages(pdf_path)
        sections = _structure_pages(pages)
        full_text = "\n\n".join(
            f"--- Page {number} ---\n{text}" for number, text in enumerate(pages, start=1)
        )

        full_text_path = pdf_path.with_suffix(".full.txt")
        structured_path = pdf_path.with_suffix(".structured.json")
        full_text_path.write_text(full_text, encoding="utf-8")
        structured_path.write_text(
            json.dumps(
                {
                    "arxiv_id": arxiv_id,
                    "pdf_url": pdf_url,
                    "page_count": len(pages),
                    "sections": sections,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        limit = max(1000, min(int(max_chars_per_section or 12000), 30000))
        returned_sections = [{
            "title": section["title"],
            "start_page": section["start_page"],
            "end_page": section["end_page"],
            "chars_total": len(section["text"]),
            "text": section["text"][:limit],
            "truncated": len(section["text"]) > limit,
        } for section in sections]

        return {
            "tool": "read_structured_paper",
            "arxiv_id": arxiv_id,
            "url": f"https://arxiv.org/abs/{arxiv_id}",
            "pdf_url": pdf_url,
            "pdf_path": str(pdf_path),
            "full_text_path": str(full_text_path),
            "structured_path": str(structured_path),
            "page_count": len(pages),
            "section_count": len(sections),
            "chars_total": len(full_text),
            "sections": returned_sections,
            "note": "All extracted text is saved locally; returned section text may be truncated to keep tool output manageable.",
        }
    except Exception as exc:
        return err("read_structured_paper", exc)


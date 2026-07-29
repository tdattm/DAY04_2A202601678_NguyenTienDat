from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from tools._shared import err, fold_text
from tools.paper_reader.tool import read_structured_paper


CATEGORY_PATTERNS = {
    "method": ("method", "methodology", "approach", "model", "architecture", "algorithm"),
    "experiments": ("experiment", "experimental setup", "evaluation", "dataset", "implementation details"),
    "results": ("result", "findings", "analysis", "ablation", "discussion"),
    "limitations": ("limitation", "limitations", "future work", "broader impact"),
}


def _category(title: str) -> str | None:
    normalized = fold_text(re.sub(r"^\s*\d+(?:\.\d+)*[.)]?\s*", "", title))
    for category, keywords in CATEGORY_PATTERNS.items():
        if any(keyword in normalized for keyword in keywords):
            return category
    return None


def extract_paper_sections(arxiv_url: str = "", max_chars_per_category: int = 16000) -> dict[str, Any]:
    try:
        structured = read_structured_paper(
            arxiv_url=arxiv_url,
            max_chars_per_section=max_chars_per_category,
        )
        if structured.get("error"):
            return structured

        stored = json.loads(Path(structured["structured_path"]).read_text(encoding="utf-8"))
        grouped: dict[str, list[dict[str, Any]]] = {name: [] for name in CATEGORY_PATTERNS}
        for section in stored.get("sections", []):
            category = _category(str(section.get("title", "")))
            if category:
                grouped[category].append({
                    "section_title": section["title"],
                    "start_page": section["start_page"],
                    "end_page": section["end_page"],
                    "text": section["text"],
                    "truncated": False,
                })

        limit = max(1000, min(int(max_chars_per_category or 16000), 40000))
        output: dict[str, Any] = {}
        for category, matches in grouped.items():
            remaining = limit
            evidence: list[dict[str, Any]] = []
            for match in matches:
                text = match["text"][:remaining]
                if not text:
                    break
                evidence.append({
                    **match,
                    "text": text,
                    "truncated": len(text) < len(match["text"]),
                })
                remaining -= len(text)
            output[category] = {
                "found": bool(matches),
                "evidence": evidence,
                "note": None if matches else f"No explicit {category} section was detected; do not infer one without evidence.",
            }

        return {
            "tool": "extract_paper_sections",
            "arxiv_id": structured["arxiv_id"],
            "url": structured["url"],
            "page_count": structured["page_count"],
            "structured_path": structured["structured_path"],
            **output,
        }
    except Exception as exc:
        return err("extract_paper_sections", exc)

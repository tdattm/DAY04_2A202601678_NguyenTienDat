---
name: paper_reader
track: core
kind: live_api
provider: arXiv
requires_env: []
inputs: [arxiv_url, max_chars_per_section]
outputs: [arxiv_id, page_count, sections, full_text_path, structured_path]
side_effect: local_file_write
---
# paper_reader

Downloads an arXiv PDF, reads every page, detects section headings, and saves
both the complete extracted text and a structured JSON artifact locally.


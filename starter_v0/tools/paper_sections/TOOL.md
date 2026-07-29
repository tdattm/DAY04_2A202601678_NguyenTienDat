---
name: paper_sections
track: core
kind: live_api
provider: arXiv
requires_env: []
inputs: [arxiv_url, max_chars_per_category]
outputs: [method, experiments, results, limitations]
side_effect: local_file_write
---
# paper_sections

Reads an arXiv paper and groups evidence under Method, Experiments, Results,
and Limitations using the paper's section headings. It returns source pages and
text rather than inventing missing sections.

---
name: explain_terms
track: core
kind: live_api
provider: arXiv and Wikipedia
requires_env: []
inputs: [arxiv_url, terms, max_contexts]
outputs: [explanations]
side_effect: local_file_write
---
# explain_terms

Finds each requested term in an arXiv paper, returns surrounding paper context,
and looks up a concise external definition from Wikipedia. External definitions
remain clearly separated from claims made by the paper.


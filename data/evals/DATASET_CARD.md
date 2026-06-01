# SupportFlow RAG/Eval Dataset Card

## Purpose

This dataset is a synthetic, scenario-driven regression suite for the SupportFlow RAG workflow. It is designed to exercise retrieval, citation, unsupported evidence, prompt injection, policy routing, action safety, and conservative review behavior.

It must not be described as a statistically representative sample of production support traffic.

## Files

- `data/sample_tickets/demo_tickets.json`: UI-visible demo tickets.
- `data/evals/supportflow_tickets.json`: eval-only tickets that keep the UI list manageable.
- `data/evals/supportflow_v1.jsonl`: fixed eval examples with references and governance metadata.
- `data/kb/*.md`: local Markdown knowledge base documents with front matter metadata.
- `docs/generated/eval-dataset-profile.md`: generated distribution and governance profile.

## Data Source and Generation

All current tickets and KB records are synthetic and hand-authored for portfolio evaluation. They are not copied from customer data. The examples are intentionally shaped around support workflow risks instead of real traffic distribution.

Every eval example records:

- `scenario`: short scenario name.
- `scenario_type`: capability or risk being exercised.
- `dataset_split`: `demo`, `regression`, or `challenge`.
- `source_type`: currently `synthetic`.
- `generation_method`: currently `hand_authored`.
- `review_status`: currently `reviewed`.
- `evidence_condition`: `supported`, `no_evidence`, `partial_evidence`, or `stale_or_draft`.
- `intended_failure_mode`: the behavior the case is meant to expose.
- `risk_level`: coarse risk label for distribution checks.
- `claims`: optional claim-to-KB support references for citation checks.

## Intended Use

Use this dataset to answer these questions:

- Did retrieval select the expected KB source or correctly return no evidence?
- Did the draft include citations when evidence exists?
- Are cited claims backed by retrieved documents?
- Did unsupported or unsafe requests route to review?
- Do weaker baselines fail in explainable ways?
- Does the graph expose conservative routing on low-risk cases that might otherwise be auto-finalized?

## Known Limitations

- The dataset is synthetic and does not measure live customer distribution.
- The lexical retriever is intentionally local and deterministic; it is not a hosted vector index.
- Claim support is evaluated through explicit fixture metadata and cited document IDs, not through a learned natural-language judge.
- Some `challenge` examples are expected to reveal current workflow limitations rather than produce a perfect graph score.
- Human review labels are authored by the project maintainer; production validation would require anonymized real-ticket samples and independent review.

## Review and Promotion Rules

New examples should not be added only because they match current model output. A new case should name the risk it covers, include expected references, and explain whether it is regression coverage or challenge coverage.

Before treating the dataset as interview evidence, run:

    python3 backend/scripts/profile_eval_dataset.py
    cd backend
    uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py

The generated profile and eval report should be used together. A high score without distribution coverage is not sufficient evidence of RAG quality.

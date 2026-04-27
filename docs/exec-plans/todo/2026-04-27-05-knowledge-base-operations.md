# Day 14 Knowledge Base Operations and Retrieval Quality

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

The MVP uses a small local Markdown knowledge base and improved lexical retrieval. After this change, the knowledge base will behave more like a managed support policy system: documents have metadata, ingestion validates them, retrieval diagnostics explain why a document was selected, and evals measure citation support.

This feature demonstrates RAG engineering beyond a toy lookup.

## Progress

- [x] (2026-04-27) Created this active ExecPlan from `docs/product-specs/ai-agent-engineer-portfolio-roadmap.md`.
- [ ] Inspect current KB Markdown files, retrieval service, and retrieval tests.
- [ ] Add KB front matter metadata and ingestion validation.
- [ ] Add retrieval diagnostics and citation support checks.
- [ ] Update API/frontend surfaces if diagnostics are user-visible.
- [ ] Extend eval reporting for retrieval and citation support.
- [ ] Update docs and this ExecPlan with observed behavior.

## Surprises & Discoveries

- Observation: No implementation discoveries yet.
  Evidence: This plan has only been created.

## Decision Log

- Decision: Start with metadata and diagnostics before vector retrieval.
  Rationale: The current KB is small. Metadata validation and explainable diagnostics provide stronger portfolio clarity than adding an embedding dependency too early.
  Date/Author: 2026-04-27 / Codex

- Decision: Keep retrieval inspectable.
  Rationale: The project is workflow-first and deterministic. Hiring reviewers should be able to understand why the agent cited a policy.
  Date/Author: 2026-04-27 / Codex

## Outcomes & Retrospective

Not started. At completion, summarize metadata schema, ingestion command, diagnostics behavior, eval updates, and any deferred vector or hybrid retrieval work.

## Context and Orientation

The local knowledge base lives under `data/kb/`. The retriever is `backend/app/services/retrieval.py`. It returns `KBHit` objects defined in `backend/app/schemas/graph.py`. Previous work improved retrieval precision with lexical token filtering and category-aware scoring.

Knowledge base front matter means a small metadata block at the top of each Markdown file. For this project, each KB document should include fields such as `doc_id`, `title`, `category`, `source_owner`, `effective_date`, `freshness`, and `policy_severity`.

Retrieval diagnostics are explanations for why documents were selected. Example diagnostic fields are score, matched terms, category boost, metadata category, and citation IDs.

## Plan of Work

First, inspect every Markdown file under `data/kb/` and the current retriever implementation. Identify the current hard-coded document metadata and move it into Markdown front matter.

Second, add a KB ingestion module such as `backend/app/services/kb_ingestion.py`. It should read Markdown files, parse front matter, validate required fields with Pydantic, and return normalized document objects. Use standard-library parsing if possible: front matter can be a simple `---` delimited block with `key: value` lines.

Third, update `backend/app/services/retrieval.py` to load documents through the ingestion module. Remove hard-coded metadata only after tests cover the new behavior.

Fourth, add diagnostics. Either extend `KBHit` with optional diagnostic fields or add a new `KBHitDiagnostic` schema attached to a separate diagnostics endpoint. If the normal API response becomes too noisy, keep regular hits small and expose diagnostics through `/api/v1/runs/{thread_id}/retrieval-diagnostics`.

Fifth, add citation verification. The first implementation can check that every draft citation corresponds to a retrieved KB document ID and that at least one cited document has lexical overlap with the draft sentence or answer. Keep it deterministic.

Sixth, update evals to report retrieval hit rate and citation support rate. If Day 13 is complete, add failure-stage integration for retrieval and citation support.

Seventh, update frontend only if diagnostics are exposed to users. Add a compact panel showing document title, score, matched terms, and category reason.

## Concrete Steps

Inspect current KB and retrieval:

    find data/kb -maxdepth 1 -type f -name '*.md' -print -exec sed -n '1,120p' {} \;
    sed -n '1,320p' backend/app/services/retrieval.py
    sed -n '1,220p' backend/tests/test_retrieval.py
    sed -n '1,260p' backend/app/evals/scoring.py

Run current backend tests:

    cd backend
    uv run --cache-dir /tmp/uv-cache pytest

After implementation, run:

    cd backend
    uv run --cache-dir /tmp/uv-cache pytest
    uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py

Manual ingestion smoke:

    cd backend
    uv run --cache-dir /tmp/uv-cache python -m app.services.kb_ingestion

Expected result: all KB Markdown files validate and print or return normalized document metadata. Temporarily remove a required field in a local test copy and confirm ingestion fails with a useful error.

## Validation and Acceptance

This plan is complete when all of these are true:

- KB Markdown files include required metadata front matter.
- A validation command or module fails clearly on missing required metadata.
- Retrieval loads metadata from KB files rather than hard-coded document maps.
- Retrieval diagnostics show score, matched terms, category boost or category match, and document IDs.
- Eval output includes citation support rate or equivalent evidence.
- Existing supported and unsupported retrieval tests pass.

## Idempotence and Recovery

KB ingestion should be read-only unless a separate build-index command is introduced. If an index file is generated, it should be deterministic and either ignored or intentionally checked in. Validation should never modify source Markdown files.

## Artifacts and Notes

This plan builds on Day 7 retrieval precision and the roadmap in `docs/product-specs/ai-agent-engineer-portfolio-roadmap.md`. It does not require external vector databases. If vector retrieval is considered, add a small spike and record the decision before adding dependencies.

## Interfaces and Dependencies

At completion, code should include a schema similar to:

    class KBDocumentMetadata(BaseModel):
        doc_id: str
        title: str
        category: Literal["billing", "account", "product", "bug", "other"]
        source_owner: str
        effective_date: str
        freshness: Literal["current", "stale", "draft"]
        policy_severity: Literal["low", "medium", "high"]

Keep parser behavior simple and documented in tests.

## Plan Revision Notes

2026-04-27: Initial active ExecPlan created by splitting the AI Agent Engineer portfolio roadmap into implementation milestones.

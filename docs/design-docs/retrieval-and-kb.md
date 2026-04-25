---
status: draft-v0.1
owner: project-maintainer
last_verified: 2026-04-24
source_of_truth_for:
  - knowledge base scope
  - ingestion
  - chunking
  - retrieval baseline
  - citation policy
  - hallucination-control behavior
---

# Retrieval and Knowledge Base Design

## 1. Purpose

This document defines the retrieval layer for `supportflow-agent`.

The goal is not to build the most advanced RAG stack in v1. The goal is to create a clear, inspectable, citation-backed retrieval path that supports support ticket drafting.

## 2. MVP scope

### In scope

- local markdown knowledge documents
- deterministic ingestion script
- chunk-level metadata
- top-k retrieval
- citations in draft replies
- fallback behavior when no evidence is found

### Out of scope for v1

- production document upload pipeline
- multi-tenant KB separation
- hybrid search
- reranker
- ACL-aware retrieval
- OCR/PDF parsing
- web search
- automatic KB rewriting

## 3. Knowledge base layout

```text
data/
  kb/
    refund_policy.md
    account_unlock.md
    bug_export_issue.md
```

Later:

```text
data/
  kb/
    billing/
    account/
    product/
    bug/
```

## 4. Document metadata

Every document should have stable metadata.

Recommended frontmatter:

```md
---
doc_id: refund_policy
title: Refund Policy
category: billing
version: 2026-04-24
source: demo
owner: support-ops
---
```

Required metadata after ingestion:

```python
class KBDocument(BaseModel):
    doc_id: str
    title: str
    category: str
    source_path: str
    version: str | None = None

class KBChunk(BaseModel):
    chunk_id: str
    doc_id: str
    title: str
    text: str
    metadata: dict
```

## 5. Chunking baseline

MVP chunking:

- split by markdown heading first
- then split long sections by character length
- target chunk size: 500-900 Chinese characters or 300-600 English words
- overlap: 50-100 characters only if sections are long

Why this baseline:

- markdown support docs are naturally sectioned
- chunk IDs can remain stable
- citations are easier to display to reviewer

Example chunk ID:

```text
refund_policy#refund-timeline#0001
```

## 6. Retrieval v0

Day2 retrieval may be lexical:

```text
score = keyword overlap + category boost + title boost
```

Inputs:

- ticket title
- ticket content
- classification category
- customer tier

Outputs:

```python
class KBHit(BaseModel):
    doc_id: str
    chunk_id: str
    title: str
    score: float
    snippet: str
    source_path: str | None = None
```

Baseline retrieval rules:

- top_k = 3
- minimum score threshold = 0.1 in lexical mode
- category match adds boost
- title match adds boost
- return empty list explicitly when no hit

## 7. Retrieval v1

After workflow works, upgrade to embedding retrieval.

Suggested local options:

- Chroma for fastest local demo
- SQLite + vector extension only if simple in your environment
- Postgres + pgvector only after DB schema is stable

Preferred 2-week path:

```text
Day2: lexical retrieval
Week1: embedding retrieval behind same RetrievalService interface
Week2: optional pgvector if time remains
```

The graph should not care which retrieval backend is used.

## 8. Retrieval service interface

```python
class RetrievalService:
    def search(
        self,
        query: str,
        category: str | None = None,
        top_k: int = 3,
    ) -> list[KBHit]:
        ...
```

Graph node should call the service:

```python
hits = retrieval_service.search(
    query=retrieval_query,
    category=state["classification"].category,
    top_k=3,
)
```

Do not put ingestion, chunking, or scoring code directly inside LangGraph nodes.

## 9. Citation policy

Every draft should follow this policy:

- If answer uses KB evidence, cite the supporting `chunk_id`.
- Citations must refer only to retrieved chunks.
- If no evidence exists, draft confidence must be low and review must be triggered.
- Never fabricate citations.
- Frontend should display citation chips and evidence snippets.

Valid draft citation:

```json
{
  "answer": "退款通常会在 1-3 个工作日内处理完成。",
  "citations": ["refund_policy#refund-timeline#0001"]
}
```

Invalid draft citation:

```json
{
  "answer": "退款今天一定到账。",
  "citations": ["company_policy"]
}
```

Problem:

- citation is too broad
- answer overclaims certainty

## 10. Hallucination-control behavior

If retrieval returns no hits:

```text
draft.suggested_action = "review"
draft.confidence <= 0.5
risk_flags includes "no_evidence"
```

Draft copy should say:

```text
当前知识库没有找到足够证据，建议人工确认后回复。
```

Do not allow the model to invent policy.

## 11. Metrics

Track these metrics:

| Metric | Meaning |
|---|---|
| retrieval_hit_rate | percentage of tickets with at least one KB hit |
| citation_coverage | percentage of drafts with citations |
| evidence_precision_sampled | sampled reviewer judgment on whether evidence supports answer |
| no_evidence_review_rate | review rate caused by missing evidence |
| avg_top_score | retrieval confidence proxy |

## 12. Test cases

Minimum cases:

1. Refund ticket retrieves refund policy.
2. Login issue retrieves account unlock guide.
3. Export button bug retrieves bug/export issue guide.
4. Unsupported question returns empty hits.
5. Draft does not cite chunks that were not retrieved.

## 13. Implementation phases

| Phase | Retrieval capability |
|---|---|
| Day2 | lexical top-k retrieval |
| Day3 | citation display in UI |
| Week1 | ingestion script + stable chunk IDs |
| Week2 | embedding backend + evaluation |

## 14. Interview talking points

Strong answer:

> I started with a simple retrieval baseline because the project first needs a reliable workflow and evidence chain. The retrieval layer is behind a service interface, so I can later replace lexical search with embedding retrieval without changing the LangGraph graph.

Weak answer:

> I used RAG because every LLM app needs RAG.

## 15. Update triggers

Update this document when:

- changing document format
- changing chunking strategy
- changing retrieval backend
- changing citation rules
- adding new KB categories
- adding vector DB or reranker

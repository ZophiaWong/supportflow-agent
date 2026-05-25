import re

from app.schemas.graph import KBHit
from app.services.kb_ingestion import KBDocument, load_kb_documents

WORD_RE = re.compile(r"[a-z0-9]+")
STOPWORDS = {
    "about",
    "after",
    "all",
    "and",
    "any",
    "are",
    "before",
    "but",
    "can",
    "for",
    "from",
    "has",
    "have",
    "how",
    "into",
    "need",
    "not",
    "now",
    "our",
    "out",
    "the",
    "this",
    "was",
    "we",
    "when",
    "which",
    "with",
    "you",
    "your",
}
SUPPORT_GENERIC_TERMS = {
    "account",
    "customer",
    "details",
    "help",
    "issue",
    "question",
    "request",
    "support",
    "team",
}
MIN_TOKEN_LENGTH = 3
MIN_OVERLAP_WITHOUT_CATEGORY = 2
MIN_SCORE = 0.1
CATEGORY_BOOST = 0.35


def _tokenize(text: str) -> set[str]:
    return {
        token
        for token in WORD_RE.findall(text.lower())
        if len(token) >= MIN_TOKEN_LENGTH
        and token not in STOPWORDS
        and token not in SUPPORT_GENERIC_TERMS
    }


def _extract_snippet(content: str) -> str:
    for block in content.split("\n\n"):
        snippet = block.strip()
        if snippet and not snippet.startswith("#"):
            return snippet.replace("\n", " ")[:220]
    return content.strip().replace("\n", " ")[:220]


def _searchable_text(document: KBDocument) -> str:
    return " ".join(
        [
            document.title,
            document.content,
            document.doc_id.replace("_", " "),
            document.metadata.source_owner,
        ]
    )


def retrieve_knowledge(
    query: str,
    *,
    category: str | None = None,
    top_k: int = 3,
) -> list[KBHit]:
    query_terms = _tokenize(query)
    if not query_terms:
        return []

    scored_hits: list[tuple[float, KBHit]] = []
    for document in load_kb_documents():
        document_terms = _tokenize(_searchable_text(document))
        overlap = query_terms & document_terms
        if not overlap:
            continue

        category_matches = category is not None and category == document.category
        if not category_matches and len(overlap) < MIN_OVERLAP_WITHOUT_CATEGORY:
            continue

        raw_score = len(overlap) / len(query_terms)
        category_boost = CATEGORY_BOOST if category_matches else 0.0
        score = round(raw_score + category_boost, 4)
        if score < MIN_SCORE:
            continue

        metadata = document.metadata
        hit = KBHit(
            doc_id=document.doc_id,
            title=document.title,
            score=score,
            snippet=_extract_snippet(document.content),
            category=metadata.category,
            source_owner=metadata.source_owner,
            effective_date=metadata.effective_date,
            freshness=metadata.freshness,
            policy_severity=metadata.policy_severity,
            matched_terms=sorted(overlap),
            category_match=category_matches,
            category_boost=category_boost,
            citation_id=document.doc_id,
        )
        scored_hits.append((score, hit))

    scored_hits.sort(key=lambda item: (-item[0], item[1].title))
    return [hit for _, hit in scored_hits[:top_k]]

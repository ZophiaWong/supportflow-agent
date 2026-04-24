import re
from functools import lru_cache
from pathlib import Path

from app.schemas.graph import KBHit

KB_PATH = Path(__file__).resolve().parents[3] / "data" / "kb"
WORD_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> set[str]:
    return {token for token in WORD_RE.findall(text.lower()) if len(token) > 1}


def _extract_title(content: str, path: Path) -> str:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped.removeprefix("# ").strip()
    return path.stem.replace("_", " ").title()


def _extract_snippet(content: str) -> str:
    for block in content.split("\n\n"):
        snippet = block.strip()
        if snippet and not snippet.startswith("#"):
            return snippet.replace("\n", " ")[:220]
    return content.strip().replace("\n", " ")[:220]


@lru_cache(maxsize=1)
def _load_kb_documents() -> tuple[dict[str, str], ...]:
    documents: list[dict[str, str]] = []
    for path in sorted(KB_PATH.glob("*.md")):
        content = path.read_text()
        documents.append(
            {
                "doc_id": path.stem,
                "title": _extract_title(content, path),
                "content": content,
                "snippet": _extract_snippet(content),
            }
        )
    return tuple(documents)


def retrieve_knowledge(query: str, *, top_k: int = 3) -> list[KBHit]:
    query_terms = _tokenize(query)
    if not query_terms:
        return []

    scored_hits: list[tuple[float, KBHit]] = []
    for document in _load_kb_documents():
        searchable_text = " ".join(
            [document["title"], document["content"], document["doc_id"].replace("_", " ")]
        )
        document_terms = _tokenize(searchable_text)
        overlap = query_terms & document_terms
        if not overlap:
            continue

        score = round(len(overlap) / len(query_terms), 4)
        hit = KBHit(
            doc_id=document["doc_id"],
            title=document["title"],
            score=score,
            snippet=document["snippet"],
        )
        scored_hits.append((score, hit))

    scored_hits.sort(key=lambda item: (-item[0], item[1].title))
    return [hit for _, hit in scored_hits[:top_k]]

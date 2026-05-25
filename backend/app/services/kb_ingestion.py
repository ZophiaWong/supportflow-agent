from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

KB_PATH = Path(__file__).resolve().parents[3] / "data" / "kb"


class KBDocumentMetadata(BaseModel):
    doc_id: str
    title: str
    category: Literal["billing", "account", "product", "bug", "other"]
    source_owner: str
    effective_date: str
    freshness: Literal["current", "stale", "draft"]
    policy_severity: Literal["low", "medium", "high"]


class KBDocument(BaseModel):
    metadata: KBDocumentMetadata
    content: str
    source_path: str

    @property
    def doc_id(self) -> str:
        return self.metadata.doc_id

    @property
    def title(self) -> str:
        return self.metadata.title

    @property
    def category(self) -> str:
        return self.metadata.category


def _parse_front_matter(raw_text: str, path: Path) -> tuple[dict[str, str], str]:
    lines = raw_text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{path}: missing front matter block")

    metadata: dict[str, str] = {}
    end_index: int | None = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"{path}: invalid front matter line {index + 1}: {line!r}")
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()

    if end_index is None:
        raise ValueError(f"{path}: front matter block is not closed")

    body = "\n".join(lines[end_index + 1 :]).strip()
    if not body:
        raise ValueError(f"{path}: document body is empty")
    return metadata, body


def load_kb_document(path: Path) -> KBDocument:
    metadata_payload, body = _parse_front_matter(path.read_text(), path)
    metadata = KBDocumentMetadata.model_validate(metadata_payload)
    document = KBDocument(
        metadata=metadata,
        content=body,
        source_path=str(path),
    )
    expected_doc_id = path.stem
    if document.doc_id != expected_doc_id:
        raise ValueError(
            f"{path}: doc_id {document.doc_id!r} must match filename stem {expected_doc_id!r}"
        )
    return document


@lru_cache(maxsize=1)
def load_kb_documents(kb_path: Path = KB_PATH) -> tuple[KBDocument, ...]:
    documents = tuple(
        load_kb_document(path)
        for path in sorted(kb_path.glob("*.md"))
    )
    if not documents:
        raise ValueError(f"No KB Markdown files found in {kb_path}")
    return documents


def validate_kb(kb_path: Path = KB_PATH) -> tuple[KBDocument, ...]:
    load_kb_documents.cache_clear()
    return load_kb_documents(kb_path)


def main() -> None:
    documents = validate_kb()
    for document in documents:
        metadata = document.metadata
        print(
            f"{metadata.doc_id} title={metadata.title!r} "
            f"category={metadata.category} freshness={metadata.freshness} "
            f"severity={metadata.policy_severity}"
        )


if __name__ == "__main__":
    main()

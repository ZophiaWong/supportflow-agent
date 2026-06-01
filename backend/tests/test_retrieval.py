from pathlib import Path

import pytest

from app.services.kb_ingestion import load_kb_document, validate_kb
from app.services.retrieval import retrieve_knowledge


def test_kb_ingestion_validates_front_matter_metadata() -> None:
    documents = validate_kb()
    by_doc_id = {document.doc_id: document for document in documents}

    assert by_doc_id["refund_policy"].metadata.category == "billing"
    assert by_doc_id["account_unlock"].metadata.source_owner == "identity-support"
    assert by_doc_id["annual_plan_seats"].metadata.freshness == "current"
    assert by_doc_id["stale_refund_exception_draft"].metadata.freshness == "draft"
    assert by_doc_id["privacy_payment_data_incident"].metadata.policy_severity == "high"


def test_kb_ingestion_fails_on_missing_required_metadata(tmp_path: Path) -> None:
    invalid_doc = tmp_path / "broken.md"
    invalid_doc.write_text(
        "---\n"
        "doc_id: broken\n"
        "title: Broken\n"
        "category: other\n"
        "---\n\n"
        "# Broken\n\n"
        "Missing required owner and freshness metadata.\n"
    )

    with pytest.raises(ValueError, match="source_owner"):
        load_kb_document(invalid_doc)


def test_retrieve_knowledge_returns_expected_supported_documents() -> None:
    examples = [
        ("duplicate charge refund invoice", "billing", "refund_policy"),
        ("administrator locked out password reset", "account", "account_unlock"),
        ("mfa device lost recovery login", "account", "mfa_recovery"),
        ("temporary seat increase annual onboarding", "product", "annual_plan_seats"),
        ("enterprise sso setup identity provider metadata", "product", "enterprise_sso_setup"),
        ("export failed csv report error", "bug", "bug_export_issue"),
        ("outage security incident data loss escalation", "bug", "incident_escalation_runbook"),
        ("legal payment data loss request", "other", "privacy_payment_data_incident"),
    ]

    for query, category, expected_doc_id in examples:
        hits = retrieve_knowledge(query, category=category)

        assert hits
        assert hits[0].doc_id == expected_doc_id
        assert hits[0].category == category
        assert hits[0].category_match is True
        assert hits[0].category_boost > 0
        assert hits[0].matched_terms
        assert hits[0].citation_id == expected_doc_id


def test_retrieve_knowledge_returns_no_hits_for_unsupported_queries() -> None:
    unsupported_queries = [
        "shipping address for physical welcome kit",
        "travel visa hotel booking question",
        "predictive churn scoring model for analytics team",
    ]

    for query in unsupported_queries:
        assert retrieve_knowledge(query, category="other") == []

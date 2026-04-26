from app.services.retrieval import retrieve_knowledge


def test_retrieve_knowledge_returns_expected_supported_documents() -> None:
    examples = [
        ("duplicate charge refund invoice", "billing", "refund_policy"),
        ("administrator locked out password reset", "account", "account_unlock"),
        ("temporary seat increase annual onboarding", "product", "annual_plan_seats"),
        ("export failed csv report error", "bug", "bug_export_issue"),
    ]

    for query, category, expected_doc_id in examples:
        hits = retrieve_knowledge(query, category=category)

        assert hits
        assert hits[0].doc_id == expected_doc_id


def test_retrieve_knowledge_returns_no_hits_for_unsupported_queries() -> None:
    unsupported_queries = [
        "shipping address for physical welcome kit",
        "travel visa hotel booking question",
        "records missing after data loss incident workspace",
    ]

    for query in unsupported_queries:
        assert retrieve_knowledge(query, category="other") == []

import pytest
import requests

from app.graph.nodes.classify_ticket import classify_ticket
from app.graph.nodes.draft_reply import draft_reply
from app.schemas.graph import KBHit, TicketClassification
from app.services import llm


class StubResponse:
    def __init__(
        self,
        *,
        status_code: int = 200,
        payload: dict[str, object] | None = None,
        text: str = "",
        json_error: ValueError | None = None,
    ) -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text
        self._json_error = json_error

    def json(self) -> dict[str, object]:
        if self._json_error is not None:
            raise self._json_error
        return self._payload


def _completion_payload(content: dict[str, object] | str) -> dict[str, object]:
    return {
        "choices": [
            {
                "message": {
                    "content": content,
                }
            }
        ]
    }


def _sample_hit(doc_id: str = "annual_plan_seats") -> KBHit:
    return KBHit(
        doc_id=doc_id,
        title="Annual Plan Seats",
        score=1.0,
        snippet="Annual plans can add seats from the account settings page.",
        category="product",
    )


def test_llm_config_loads_root_dotenv_without_overriding_env(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "SUPPORTFLOW_LLM_ENABLED=true",
                "SUPPORTFLOW_LLM_MODEL=from-dotenv",
                "SUPPORTFLOW_LLM_TIMEOUT_SECONDS=12",
                "",
            ]
        )
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SUPPORTFLOW_LLM_ENABLED", raising=False)
    monkeypatch.delenv("SUPPORTFLOW_LLM_TIMEOUT_SECONDS", raising=False)
    monkeypatch.setenv("SUPPORTFLOW_LLM_MODEL", "from-env")
    monkeypatch.setattr(llm, "ENV_LOADED", False)

    assert llm.llm_enabled() is True
    assert llm._model_name() == "from-env"
    assert llm._timeout_seconds() == 12


def test_generate_draft_reply_returns_structured_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SUPPORTFLOW_LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def post(*_: object, **kwargs: object) -> StubResponse:
        assert kwargs["json"]["model"] == "gpt-4o-mini"  # type: ignore[index]
        assert str(_[0]).endswith("/chat/completions")
        response_format = kwargs["json"]["response_format"]  # type: ignore[index]
        assert response_format["type"] == "json_schema"
        assert response_format["json_schema"]["strict"] is True
        schema = response_format["json_schema"]["schema"]
        assert schema["additionalProperties"] is False
        assert schema["required"] == ["answer", "citations", "confidence"]
        assert sorted(schema["properties"]) == ["answer", "citations", "confidence"]
        return StubResponse(
            payload=_completion_payload(
                {
                    "answer": "Hi Jamie, you can add seats from account settings.",
                    "citations": ["annual_plan_seats"],
                    "confidence": 0.9,
                }
            )
        )

    monkeypatch.setattr(requests, "post", post)

    result = llm.generate_draft_reply(
        ticket={
            "subject": "Add seats",
            "preview": "Can I add seats to our annual plan?",
            "customer_name": "Jamie",
        },
        classification=TicketClassification(
            category="product",
            priority="P3",
            reason="Plan seat question.",
        ),
        retrieved_chunks=[_sample_hit()],
    )

    assert result.value is not None
    assert result.error_reason is None
    assert result.value.answer.startswith("Hi Jamie")
    assert result.value.citations == ["annual_plan_seats"]
    assert result.value.confidence == 0.9


def test_draft_reply_prompt_rejects_wrapper_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SUPPORTFLOW_LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def post(*_: object, **kwargs: object) -> StubResponse:
        system_message = kwargs["json"]["messages"][0]["content"]  # type: ignore[index]
        assert "top-level keys answer, citations, and confidence" in system_message
        assert "Do not use response, message, text, markdown, or wrapper objects" in system_message
        return StubResponse(
            payload=_completion_payload(
                {
                    "answer": "Hi Jamie, seats can be added from account settings.",
                    "citations": ["annual_plan_seats"],
                    "confidence": 0.9,
                }
            )
        )

    monkeypatch.setattr(requests, "post", post)

    result = llm.generate_draft_reply(
        ticket={"subject": "Add seats", "preview": "Can I add seats?"},
        classification=TicketClassification(
            category="product",
            priority="P3",
            reason="Plan seat question.",
        ),
        retrieved_chunks=[_sample_hit()],
    )

    assert result.value is not None
    assert result.error_reason is None


def test_generate_draft_reply_records_http_403(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("SUPPORTFLOW_LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        requests,
        "post",
        lambda *_args, **_kwargs: StubResponse(
            status_code=403,
            text='{"error":{"message":"model access denied"}}',
        ),
    )

    result = llm.generate_draft_reply(
        ticket={
            "subject": "Add seats",
            "preview": "Can I add seats to our annual plan?",
            "customer_name": "Jamie",
        },
        classification=TicketClassification(
            category="product",
            priority="P3",
            reason="Plan seat question.",
        ),
        retrieved_chunks=[_sample_hit()],
    )

    assert result.value is None
    assert result.error_reason == "http_403"
    assert "model access denied" in (result.error_detail or "")
    assert "LLM call fell back to deterministic behavior" in caplog.text
    assert "reason=http_403" in caplog.text
    assert "status=403" in caplog.text


def test_generate_draft_reply_records_request_failure(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("SUPPORTFLOW_LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def post(*_: object, **__: object) -> StubResponse:
        raise requests.exceptions.Timeout("timed out")

    monkeypatch.setattr(requests, "post", post)

    result = llm.generate_draft_reply(
        ticket={"subject": "Add seats", "preview": "Can I add seats?"},
        classification=TicketClassification(
            category="product",
            priority="P3",
            reason="Plan seat question.",
        ),
        retrieved_chunks=[_sample_hit()],
    )

    assert result.value is None
    assert result.error_reason == "request_failed"
    assert "timed out" in (result.error_detail or "")
    assert "LLM call fell back to deterministic behavior" in caplog.text
    assert "reason=request_failed" in caplog.text


def test_generate_draft_reply_records_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SUPPORTFLOW_LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        requests,
        "post",
        lambda *_args, **_kwargs: StubResponse(
            text="not json",
            json_error=ValueError("bad json"),
        ),
    )

    result = llm.generate_draft_reply(
        ticket={"subject": "Add seats", "preview": "Can I add seats?"},
        classification=TicketClassification(
            category="product",
            priority="P3",
            reason="Plan seat question.",
        ),
        retrieved_chunks=[_sample_hit()],
    )

    assert result.value is None
    assert result.error_reason == "invalid_json"


def test_generate_draft_reply_records_schema_validation_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SUPPORTFLOW_LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        requests,
        "post",
        lambda *_args, **_kwargs: StubResponse(
            payload=_completion_payload({"answer": "Missing required fields."})
        ),
    )

    result = llm.generate_draft_reply(
        ticket={"subject": "Add seats", "preview": "Can I add seats?"},
        classification=TicketClassification(
            category="product",
            priority="P3",
            reason="Plan seat question.",
        ),
        retrieved_chunks=[_sample_hit()],
    )

    assert result.value is None
    assert result.error_reason == "schema_validation_failed"
    assert "payload_keys=['answer']" in (result.error_detail or "")


def test_generate_draft_reply_rejects_provider_wrapped_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SUPPORTFLOW_LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    wrapped_text = (
        "Hello Morgan, thank you for reaching out. Support can confirm your current "
        "seat count and plan end date so we can assist you further."
    )
    monkeypatch.setattr(
        requests,
        "post",
        lambda *_args, **_kwargs: StubResponse(
            payload=_completion_payload({"response": wrapped_text})
        ),
    )

    result = llm.generate_draft_reply(
        ticket={"subject": "Seat count", "preview": "Can you confirm our seats?"},
        classification=TicketClassification(
            category="product",
            priority="P3",
            reason="Plan seat question.",
        ),
        retrieved_chunks=[_sample_hit()],
    )

    assert result.value is None
    assert result.error_reason == "schema_validation_failed"
    assert "payload_keys=['response']" in (result.error_detail or "")
    assert wrapped_text not in (result.error_detail or "")


def test_generate_draft_reply_rejects_unknown_citations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SUPPORTFLOW_LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        requests,
        "post",
        lambda *_args, **_kwargs: StubResponse(
            payload=_completion_payload(
                {
                    "answer": "Unsupported answer.",
                    "citations": ["made_up_doc"],
                    "confidence": 0.9,
                }
            )
        ),
    )

    result = llm.generate_draft_reply(
        ticket={"subject": "Add seats", "preview": "Can I add seats?"},
        classification=TicketClassification(
            category="product",
            priority="P3",
            reason="Plan seat question.",
        ),
        retrieved_chunks=[_sample_hit()],
    )

    assert result.value is None
    assert result.error_reason == "unknown_citations"


def test_draft_reply_falls_back_when_llm_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SUPPORTFLOW_LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def post(*_: object, **__: object) -> StubResponse:
        raise requests.exceptions.Timeout("boom")

    monkeypatch.setattr(requests, "post", post)

    result = draft_reply(
        {
            "ticket": {
                "subject": "Add seats",
                "preview": "Can I add seats to our annual plan?",
                "customer_name": "Jamie",
            },
            "classification": TicketClassification(
                category="product",
                priority="P3",
                reason="Plan seat question.",
            ),
            "retrieved_chunks": [_sample_hit()],
        }
    )

    assert result["current_node"] == "draft_reply"
    assert result["draft_source"] == "fallback"
    assert result["draft_llm_error"] == "request_failed"
    assert result["draft"].citations == ["annual_plan_seats"]
    assert "Annual Plan Seats" in result["draft"].answer


def test_draft_reply_marks_llm_source(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SUPPORTFLOW_LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        requests,
        "post",
        lambda *_args, **_kwargs: StubResponse(
            payload=_completion_payload(
                {
                    "answer": "Hi Jamie, seats can be added from account settings.",
                    "citations": ["annual_plan_seats"],
                    "confidence": 0.9,
                }
            )
        ),
    )

    result = draft_reply(
        {
            "ticket": {
                "subject": "Add seats",
                "preview": "Can I add seats to our annual plan?",
                "customer_name": "Jamie",
            },
            "classification": TicketClassification(
                category="product",
                priority="P3",
                reason="Plan seat question.",
            ),
            "retrieved_chunks": [_sample_hit()],
        }
    )

    assert result["draft_source"] == "llm"
    assert "draft_llm_error" not in result
    assert result["draft"].confidence == 0.9


def test_draft_reply_falls_back_when_provider_wraps_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SUPPORTFLOW_LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        requests,
        "post",
        lambda *_args, **_kwargs: StubResponse(
            payload=_completion_payload(
                {
                    "response": (
                        "Hello Morgan, thank you for reaching out. Support can confirm "
                        "your current seat count."
                    )
                }
            )
        ),
    )

    result = draft_reply(
        {
            "ticket": {
                "subject": "Seat count",
                "preview": "Can you confirm our seats?",
                "customer_name": "Morgan",
            },
            "classification": TicketClassification(
                category="product",
                priority="P3",
                reason="Plan seat question.",
            ),
            "retrieved_chunks": [_sample_hit()],
        }
    )

    assert result["draft_source"] == "fallback"
    assert result["draft_llm_error"] == "schema_validation_failed"
    assert result["draft"].citations == ["annual_plan_seats"]


def test_draft_reply_without_kb_keeps_low_confidence_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SUPPORTFLOW_LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def post(*_: object, **__: object) -> StubResponse:
        raise requests.exceptions.Timeout("boom")

    monkeypatch.setattr(requests, "post", post)

    result = draft_reply(
        {
            "ticket": {
                "subject": "Unknown request",
                "preview": "Can you help with something unusual?",
                "customer_name": "Jamie",
            },
            "classification": TicketClassification(
                category="other",
                priority="P2",
                reason="No clear category.",
            ),
            "retrieved_chunks": [],
        }
    )

    assert result["draft"].citations == []
    assert result["draft"].confidence == 0.35
    assert result["draft_source"] == "fallback"


def test_classify_ticket_uses_structured_llm_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SUPPORTFLOW_LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        requests,
        "post",
        lambda *_args, **_kwargs: StubResponse(
            payload=_completion_payload(
                {
                    "category": "account",
                    "priority": "P1",
                    "reason": "Customer is locked out of the admin account.",
                }
            )
        ),
    )

    result = classify_ticket(
        {
            "ticket": {
                "subject": "Need urgent admin access",
                "preview": "We are locked out.",
                "priority": "high",
            }
        }
    )

    assert result["classification"].category == "account"
    assert result["classification"].priority == "P1"
    assert result["classification_source"] == "llm"
    assert "classification_llm_error" not in result


def test_classify_ticket_accepts_llm_output_without_reason(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SUPPORTFLOW_LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        requests,
        "post",
        lambda *_args, **_kwargs: StubResponse(
            payload=_completion_payload(
                {
                    "category": "account",
                    "priority": "P0",
                }
            )
        ),
    )

    result = classify_ticket(
        {
            "ticket": {
                "subject": "Cannot access admin",
                "preview": "We are locked out.",
                "priority": "urgent",
            }
        }
    )

    assert result["classification"].category == "account"
    assert result["classification"].priority == "P0"
    assert result["classification"].reason == "LLM classified ticket as account / P0."
    assert result["classification_source"] == "llm"
    assert "classification_llm_error" not in result


def test_classify_ticket_falls_back_to_rules_when_llm_output_is_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SUPPORTFLOW_LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        requests,
        "post",
        lambda *_args, **_kwargs: StubResponse(
            payload=_completion_payload(
                {
                    "category": "unsupported",
                    "priority": "P1",
                    "reason": "Invalid category.",
                }
            )
        ),
    )

    result = classify_ticket(
        {
            "ticket": {
                "subject": "Need invoice help",
                "preview": "There is a billing charge question.",
                "priority": "medium",
            }
        }
    )

    assert result["classification"].category == "billing"
    assert result["classification"].priority == "P2"
    assert result["classification_source"] == "fallback"
    assert result["classification_llm_error"] == "schema_validation_failed"

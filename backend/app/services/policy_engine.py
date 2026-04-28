from typing import Literal

from app.schemas.actions import SupportAction
from app.schemas.graph import (
    DraftReply,
    KBHit,
    PolicyAssessment,
    PolicyCheckResult,
    TicketClassification,
)

HIGH_RISK_KEYWORDS = (
    "refund",
    "payment",
    "account unlock",
    "locked out",
    "legal",
    "outage",
    "data loss",
)

PROMPT_INJECTION_MARKERS = (
    "ignore previous",
    "disregard previous",
    "override instructions",
    "system prompt",
    "developer message",
    "share admin password",
)

LEGAL_SECURITY_MARKERS = (
    "legal",
    "security",
    "payment data",
    "data loss",
    "admin password",
)


def _join_ticket_text(ticket: dict[str, object]) -> str:
    return " ".join(
        [
            str(ticket.get("subject", "")),
            str(ticket.get("preview", "")),
        ]
    ).lower()


def _result(
    *,
    policy_id: str,
    severity: Literal["info", "warning", "blocker"],
    passed: bool,
    message: str,
    evidence: list[str] | None = None,
) -> PolicyCheckResult:
    return PolicyCheckResult(
        policy_id=policy_id,
        severity=severity,
        passed=passed,
        message=message,
        evidence=evidence or [],
    )


def evaluate_policy(
    *,
    ticket: dict[str, object],
    classification: TicketClassification,
    retrieved_chunks: list[KBHit],
    draft: DraftReply,
    proposed_actions: list[SupportAction] | None = None,
) -> PolicyAssessment:
    text = _join_ticket_text(ticket)
    kb_text = " ".join(hit.snippet for hit in retrieved_chunks).lower()
    combined_input = f"{text} {kb_text}"
    actions = proposed_actions or []
    retrieved_doc_ids = {hit.doc_id for hit in retrieved_chunks}
    citation_ids = set(draft.citations)

    injection_markers = [
        marker for marker in PROMPT_INJECTION_MARKERS if marker in combined_input
    ]
    high_risk_terms = [keyword for keyword in HIGH_RISK_KEYWORDS if keyword in text]
    legal_security_terms = [
        marker for marker in LEGAL_SECURITY_MARKERS if marker in text
    ]
    high_impact_actions = [
        action.action_type for action in actions if action.requires_review
    ]

    results = [
        _result(
            policy_id="priority_requires_review",
            severity="warning",
            passed=classification.priority not in {"P0", "P1"},
            message=(
                "Ticket priority is low enough for normal handling."
                if classification.priority not in {"P0", "P1"}
                else "High-priority tickets require human review."
            ),
            evidence=[classification.priority],
        ),
        _result(
            policy_id="low_confidence",
            severity="warning",
            passed=draft.confidence >= 0.75,
            message=(
                "Draft confidence meets the policy threshold."
                if draft.confidence >= 0.75
                else "Draft confidence is below the policy threshold."
            ),
            evidence=[f"{draft.confidence:.2f}"],
        ),
        _result(
            policy_id="no_evidence",
            severity="blocker",
            passed=bool(retrieved_chunks),
            message=(
                "Knowledge evidence is available."
                if retrieved_chunks
                else "No knowledge evidence was retrieved for this ticket."
            ),
            evidence=sorted(retrieved_doc_ids),
        ),
        _result(
            policy_id="missing_citations",
            severity="warning",
            passed=not retrieved_chunks or bool(citation_ids & retrieved_doc_ids),
            message=(
                "The draft cites retrieved knowledge."
                if not retrieved_chunks or bool(citation_ids & retrieved_doc_ids)
                else "The draft does not cite any retrieved knowledge."
            ),
            evidence=sorted(citation_ids),
        ),
        _result(
            policy_id="billing_sensitive",
            severity="warning",
            passed=classification.category != "billing" or draft.confidence >= 0.85,
            message=(
                "Billing-sensitive confidence review is not required."
                if classification.category != "billing" or draft.confidence >= 0.85
                else "Billing drafts below 0.85 confidence require review."
            ),
            evidence=[classification.category, f"{draft.confidence:.2f}"],
        ),
        _result(
            policy_id="sensitive_request",
            severity="warning",
            passed=not high_risk_terms,
            message=(
                "No sensitive request terms matched."
                if not high_risk_terms
                else "Sensitive request terms require reviewer inspection."
            ),
            evidence=high_risk_terms,
        ),
        _result(
            policy_id="prompt_injection",
            severity="blocker",
            passed=not injection_markers,
            message=(
                "No prompt-injection language matched."
                if not injection_markers
                else "Customer or knowledge text contains instruction-override language."
            ),
            evidence=injection_markers,
        ),
        _result(
            policy_id="legal_or_security_risk",
            severity="blocker",
            passed=not legal_security_terms,
            message=(
                "No legal or security terms matched."
                if not legal_security_terms
                else "Legal, security, or account-risk language requires review."
            ),
            evidence=legal_security_terms,
        ),
        _result(
            policy_id="high_impact_action_requires_review",
            severity="warning",
            passed=not high_impact_actions,
            message=(
                "No high-impact support actions were proposed."
                if not high_impact_actions
                else "One or more proposed support actions require human approval."
            ),
            evidence=high_impact_actions,
        ),
    ]

    failed_policy_ids = [result.policy_id for result in results if not result.passed]
    return PolicyAssessment(
        review_required=bool(failed_policy_ids),
        failed_policy_ids=failed_policy_ids,
        results=results,
    )

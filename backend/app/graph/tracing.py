from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from langgraph.errors import GraphInterrupt

from app.graph.state import TicketState
from app.schemas.actions import SupportAction
from app.schemas.graph import PolicyAssessment, RunTraceEvent
from app.services.run_trace_store import get_run_trace_store


GraphNode = Callable[[TicketState], TicketState]


def _now() -> datetime:
    return datetime.now(UTC)


def _duration_ms(started_at: datetime, ended_at: datetime) -> int:
    return max(0, round((ended_at - started_at).total_seconds() * 1000))


def _action_attributes(actions: list[SupportAction] | None) -> list[dict[str, object]]:
    return [
        {
            "action_id": action.action_id,
            "action_type": action.action_type,
            "status": action.status,
            "requires_review": action.requires_review,
        }
        for action in actions or []
    ]


def _policy_attributes(assessment: PolicyAssessment | None) -> dict[str, object]:
    if assessment is None:
        return {}

    failed_results = [
        result for result in assessment.results if result.policy_id in assessment.failed_policy_ids
    ]
    return {
        "policy_review_required": assessment.review_required,
        "failed_policy_ids": assessment.failed_policy_ids,
        "policy_severities": {
            result.policy_id: result.severity for result in failed_results
        },
    }


def _summarize_node(node_name: str, values: Mapping[str, Any]) -> str:
    if node_name == "load_ticket_context":
        return "Loaded ticket context."
    if node_name == "classify_ticket":
        classification = values.get("classification")
        if classification is not None:
            return f"Classified ticket as {classification.category} / {classification.priority}."
    if node_name == "retrieve_knowledge":
        return f"Retrieved {len(values.get('retrieved_chunks', []))} knowledge chunks."
    if node_name == "draft_reply":
        draft = values.get("draft")
        if draft is not None:
            return f"Generated draft with confidence {draft.confidence:.2f}."
    if node_name == "propose_actions":
        return f"Proposed {len(values.get('proposed_actions', []))} support actions."
    if node_name == "risk_gate":
        policy_assessment = values.get("policy_assessment")
        if policy_assessment is not None:
            return (
                f"Policy evaluation found {len(policy_assessment.failed_policy_ids)} "
                "failed checks."
            )
    if node_name == "human_review_interrupt":
        review_decision = values.get("review_decision")
        if review_decision is not None:
            return f"Received reviewer decision: {review_decision.decision}."
        return "Paused workflow for human review."
    if node_name == "apply_review_decision":
        review_decision = values.get("review_decision")
        if review_decision is not None:
            return f"Applied reviewer decision: {review_decision.decision}."
    if node_name == "finalize_reply":
        final_response = values.get("final_response")
        if final_response is not None:
            return f"Finalized reply with disposition {final_response.disposition}."
    if node_name == "manual_takeover":
        return "Moved workflow to manual takeover."
    return f"Executed {node_name}."


def _attributes_for_node(node_name: str, values: Mapping[str, Any]) -> dict[str, object]:
    attributes: dict[str, object] = {}

    classification = values.get("classification")
    if classification is not None:
        attributes["classification_category"] = classification.category
        attributes["classification_priority"] = classification.priority

    retrieved_chunks = values.get("retrieved_chunks")
    if retrieved_chunks is not None:
        attributes["retrieved_doc_ids"] = [hit.doc_id for hit in retrieved_chunks]
        attributes["retrieved_chunk_count"] = len(retrieved_chunks)

    draft = values.get("draft")
    if draft is not None:
        attributes["draft_confidence"] = draft.confidence
        attributes["draft_citations"] = draft.citations

    risk_assessment = values.get("risk_assessment")
    if risk_assessment is not None:
        attributes["review_required"] = risk_assessment.review_required
        attributes["risk_flags"] = risk_assessment.risk_flags

    attributes.update(_policy_attributes(values.get("policy_assessment")))

    proposed_actions = values.get("proposed_actions")
    if proposed_actions is not None:
        attributes["proposed_actions"] = _action_attributes(proposed_actions)
        attributes["proposed_action_ids"] = [
            action.action_id for action in proposed_actions
        ]
        attributes["proposed_action_types"] = [
            action.action_type for action in proposed_actions
        ]
        attributes["action_statuses"] = {
            action.action_id: action.status for action in proposed_actions
        }

    executed_actions = values.get("executed_actions")
    if executed_actions is not None:
        attributes["executed_actions"] = _action_attributes(executed_actions)
        attributes["executed_action_ids"] = [
            action.action_id for action in executed_actions
        ]
        attributes["executed_action_types"] = [
            action.action_type for action in executed_actions
        ]

    review_decision = values.get("review_decision")
    if review_decision is not None:
        attributes["review_decision"] = review_decision.decision
        attributes["reviewer_note_present"] = bool(review_decision.reviewer_note)
        attributes["edited_answer_present"] = bool(review_decision.edited_answer)

    final_response = values.get("final_response")
    if final_response is not None:
        attributes["final_disposition"] = final_response.disposition
        attributes["final_citations"] = final_response.citations

    status = values.get("status")
    if status is not None:
        attributes["workflow_status"] = status

    return attributes


def _record_trace_event(
    *,
    node_name: str,
    state: TicketState,
    output: TicketState | None,
    status: str,
    started_at: datetime,
    ended_at: datetime,
    error: BaseException | None = None,
) -> None:
    values: dict[str, Any] = dict(state)
    if output:
        values.update(output)

    attributes = _attributes_for_node(node_name, values)
    if error is not None and status == "failed":
        attributes["error_type"] = type(error).__name__
        attributes["error_message"] = str(error)

    get_run_trace_store().append(
        RunTraceEvent(
            trace_id=uuid4().hex,
            thread_id=str(values.get("thread_id", "")),
            ticket_id=str(values.get("ticket_id", "")),
            node_name=node_name,
            span_type="graph_node",
            status=status,  # type: ignore[arg-type]
            started_at=started_at.isoformat(),
            ended_at=ended_at.isoformat(),
            duration_ms=_duration_ms(started_at, ended_at),
            summary=(
                f"{node_name} interrupted for human input."
                if status == "interrupted"
                else (
                    f"{node_name} failed: {type(error).__name__}"
                    if status == "failed" and error is not None
                    else _summarize_node(node_name, values)
                )
            ),
            attributes=attributes,
        )
    )


def traced_node(node_name: str, node: GraphNode) -> GraphNode:
    def wrapped(state: TicketState) -> TicketState:
        started_at = _now()
        try:
            output = node(state)
        except GraphInterrupt as exc:
            ended_at = _now()
            _record_trace_event(
                node_name=node_name,
                state=state,
                output=None,
                status="interrupted",
                started_at=started_at,
                ended_at=ended_at,
                error=exc,
            )
            raise
        except Exception as exc:
            ended_at = _now()
            _record_trace_event(
                node_name=node_name,
                state=state,
                output=None,
                status="failed",
                started_at=started_at,
                ended_at=ended_at,
                error=exc,
            )
            raise

        ended_at = _now()
        _record_trace_event(
            node_name=node_name,
            state=state,
            output=output,
            status="completed",
            started_at=started_at,
            ended_at=ended_at,
        )
        return output

    return wrapped

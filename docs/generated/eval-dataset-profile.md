# Eval Dataset Profile

This generated profile summarizes the local synthetic RAG/eval dataset. It is a coverage and regression profile, not a claim about real production traffic distribution.

## Scope

- Dataset file: `data/evals/supportflow_v1.jsonl`
- KB documents: 15
- Demo tickets: 10
- Eval-only tickets: 36
- Eval examples: 39
- Claim-support references: 35

## KB Documents by Category

| Value | Count |
| --- | ---: |
| billing | 4 |
| product | 4 |
| account | 3 |
| bug | 3 |
| other | 1 |

## KB Documents by Freshness

| Value | Count |
| --- | ---: |
| current | 14 |
| draft | 1 |

## KB Documents by Policy Severity

| Value | Count |
| --- | ---: |
| high | 8 |
| medium | 5 |
| low | 2 |

## Eval Examples by Reference Category

| Value | Count |
| --- | ---: |
| account | 8 |
| billing | 8 |
| other | 8 |
| product | 8 |
| bug | 7 |

## Eval Examples by Scenario Type

| Value | Count |
| --- | ---: |
| supported_rag | 14 |
| safe_auto_finalize_reference | 8 |
| unsupported_no_evidence | 6 |
| security_incident | 5 |
| prompt_injection | 3 |
| action_safety | 1 |
| ambiguous_multi_intent | 1 |
| stale_policy | 1 |

## Eval Examples by Dataset Split

| Value | Count |
| --- | ---: |
| challenge | 20 |
| regression | 16 |
| demo | 3 |

## Eval Examples by Evidence Condition

| Value | Count |
| --- | ---: |
| supported | 31 |
| no_evidence | 6 |
| partial_evidence | 1 |
| stale_or_draft | 1 |

## Eval Examples by Intended Failure Mode

| Value | Count |
| --- | ---: |
| conservative_review_overroutes_safe_case | 8 |
| none | 8 |
| no_evidence_review | 6 |
| external_send_requires_review | 4 |
| security_escalation | 4 |
| prompt_injection_review | 3 |
| billing_receipt_policy_boundary | 2 |
| legal_account_escalation | 1 |
| multi_intent_retrieval_gap | 1 |
| stale_policy_requires_review | 1 |
| unsafe_credit_review | 1 |

## Eval Examples by Risk Level

| Value | Count |
| --- | ---: |
| high | 15 |
| medium | 13 |
| low | 11 |

## Expected Review Routing

| Value | Count |
| --- | ---: |
| True | 31 |
| False | 8 |

## Expected Terminal Status

| Value | Count |
| --- | ---: |
| waiting_review | 31 |
| done | 8 |

## Expected Retrieval Documents

| Value | Count |
| --- | ---: |
| <no expected retrieval> | 6 |
| account_unlock | 6 |
| bug_export_issue | 5 |
| refund_policy | 5 |
| annual_plan_seats | 4 |
| enterprise_sso_setup | 2 |
| export_retention_window | 2 |
| incident_escalation_runbook | 2 |
| invoice_receipt_policy | 2 |
| mfa_recovery | 2 |
| privacy_payment_data_incident | 2 |
| account_ownership_transfer | 1 |
| billing_credit_policy | 1 |
| mobile_crash_runbook | 1 |
| stale_refund_exception_draft | 1 |
| trial_plan_limits | 1 |

## Governance Checks

No metadata, ticket-reference, KB-reference, or claim-support reference issues detected.

## Interpretation Notes

- `source_type=synthetic` means these examples are hand-authored portfolio fixtures, not real customer traffic.
- `challenge` examples intentionally include cases that may expose conservative routing, partial evidence, prompt injection, stale policy, or unsupported requests.
- `safe_auto_finalize_reference` is a reference expectation for low-risk support answers; current graph behavior may still route those cases to review because customer-facing sends are approval-gated.
- Claim-support references map expected answer claims to KB document IDs so citation quality can be checked beyond citation presence.

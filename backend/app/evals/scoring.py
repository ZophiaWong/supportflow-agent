import re

from app.evals.schemas import (
    BadCaseRecord,
    EvalExample,
    EvalExampleResult,
    EvalFailureStage,
    EvalMetricResult,
    EvalRunSummary,
    EvalTargetOutput,
)

WORD_RE = re.compile(r"[a-z0-9]+")
MIN_CITATION_OVERLAP = 1


def _passed_metric(name: str, expected: object, actual: object, passed: bool) -> EvalMetricResult:
    return EvalMetricResult(
        name=name,  # type: ignore[arg-type]
        passed=passed,
        score=1.0 if passed else 0.0,
        expected=expected,
        actual=actual,
    )


def _bad_case(
    *,
    example: EvalExample,
    output: EvalTargetOutput,
    failure_type: str,
    failure_stage: EvalFailureStage,
    expected: dict[str, object],
    actual: dict[str, object],
    notes: str,
) -> BadCaseRecord:
    return BadCaseRecord(
        example_id=example.id,
        target=output.target,
        failure_type=failure_type,
        failure_stage=failure_stage,
        expected=expected,
        actual=actual,
        trace_url=output.trace_url,
        notes=notes,
    )


def _tokenize_for_support(text: str) -> set[str]:
    return {
        token
        for token in WORD_RE.findall(text.lower())
        if len(token) >= 4
    }


def _citation_support_result(
    *,
    output: EvalTargetOutput,
    citation_required: bool,
) -> tuple[bool, dict[str, object]]:
    cited_doc_ids = set(output.citations)
    retrieved_doc_ids = set(output.retrieved_doc_ids)
    unknown_citations = sorted(cited_doc_ids - retrieved_doc_ids)
    evidence_by_doc_id = output.metadata.get("retrieved_evidence_by_doc_id", {})
    answer_terms = _tokenize_for_support(output.answer or "")

    supported_citations: list[str] = []
    unsupported_citations: list[str] = []
    if isinstance(evidence_by_doc_id, dict):
        for citation in output.citations:
            evidence = evidence_by_doc_id.get(citation)
            evidence_terms = _tokenize_for_support(evidence if isinstance(evidence, str) else "")
            if answer_terms & evidence_terms:
                supported_citations.append(citation)
            else:
                unsupported_citations.append(citation)
    else:
        unsupported_citations = list(output.citations)

    if not output.citations:
        passed = not citation_required
    else:
        passed = not unknown_citations and bool(supported_citations)

    return passed, {
        "citations": output.citations,
        "retrieved_doc_ids": output.retrieved_doc_ids,
        "unknown_citations": unknown_citations,
        "supported_citations": supported_citations,
        "unsupported_citations": unsupported_citations,
    }


def _claim_support_result(example: EvalExample, output: EvalTargetOutput) -> tuple[bool | None, dict[str, object]]:
    raw_claims = example.metadata.get("claims", [])
    if not isinstance(raw_claims, list) or not raw_claims:
        return None, {"claims_evaluated": 0, "claims": []}

    retrieved_doc_ids = set(output.retrieved_doc_ids)
    cited_doc_ids = set(output.citations)
    claim_results: list[dict[str, object]] = []
    unsupported_claims: list[str] = []

    for raw_claim in raw_claims:
        if not isinstance(raw_claim, dict):
            unsupported_claims.append("<invalid-claim-metadata>")
            claim_results.append(
                {
                    "claim": "<invalid-claim-metadata>",
                    "supporting_doc_ids": [],
                    "retrieved_supporting_doc_ids": [],
                    "cited_supporting_doc_ids": [],
                    "supported": False,
                }
            )
            continue

        claim = str(raw_claim.get("claim", ""))
        supporting_doc_ids = [
            str(doc_id)
            for doc_id in raw_claim.get("supporting_doc_ids", [])
            if isinstance(doc_id, str)
        ]
        expected_support = set(supporting_doc_ids)
        retrieved_support = sorted(expected_support & retrieved_doc_ids)
        cited_support = sorted(expected_support & cited_doc_ids)
        supported = bool(retrieved_support) and bool(cited_support)
        claim_results.append(
            {
                "claim": claim,
                "supporting_doc_ids": supporting_doc_ids,
                "retrieved_supporting_doc_ids": retrieved_support,
                "cited_supporting_doc_ids": cited_support,
                "supported": supported,
            }
        )
        if not supported:
            unsupported_claims.append(claim or "<empty-claim>")

    return not unsupported_claims, {
        "claims_evaluated": len(claim_results),
        "claims": claim_results,
        "unsupported_claims": unsupported_claims,
    }


def score_example(example: EvalExample, output: EvalTargetOutput) -> EvalExampleResult:
    reference = example.reference_outputs
    metrics: list[EvalMetricResult] = []
    bad_cases: list[BadCaseRecord] = []

    if output.category_supported:
        category_passed = output.category == reference.category
        metrics.append(
            _passed_metric(
                "category_accuracy",
                reference.category,
                output.category,
                category_passed,
            )
        )
        if not category_passed:
            bad_cases.append(
                _bad_case(
                    example=example,
                    output=output,
                    failure_type="wrong_category",
                    failure_stage="classification",
                    expected={"category": reference.category},
                    actual={"category": output.category},
                    notes="Target classified the ticket differently than the fixed reference.",
                )
            )
    else:
        metrics.append(
            EvalMetricResult(
                name="category_accuracy",
                passed=None,
                score=None,
                expected=reference.category,
                actual=None,
                notes="Target does not support classification.",
            )
        )

    retrieved_expected = set(reference.should_retrieve_doc_ids)
    retrieved_actual = set(output.retrieved_doc_ids)
    retrieval_passed = (
        bool(retrieved_expected & retrieved_actual)
        if retrieved_expected
        else not retrieved_actual
    )
    metrics.append(
        _passed_metric(
            "retrieval_hit",
            reference.should_retrieve_doc_ids,
            output.retrieved_doc_ids,
            retrieval_passed,
        )
    )
    if not retrieval_passed:
        failure_type = (
            "missing_expected_retrieval"
            if retrieved_expected
            else "unexpected_retrieval"
        )
        bad_cases.append(
            _bad_case(
                example=example,
                output=output,
                failure_type=failure_type,
                failure_stage="retrieval",
                expected={"should_retrieve_doc_ids": reference.should_retrieve_doc_ids},
                actual={"retrieved_doc_ids": output.retrieved_doc_ids},
                notes=(
                    "Target did not retrieve any expected KB document."
                    if retrieved_expected
                    else "Target retrieved KB evidence when the reference expected no evidence."
                ),
            )
        )

    citation_passed = bool(output.citations) if reference.must_include_citation else True
    metrics.append(
        _passed_metric(
            "citation_coverage",
            {"must_include_citation": reference.must_include_citation},
            {"citations": output.citations},
            citation_passed,
        )
    )
    if not citation_passed:
        bad_cases.append(
            _bad_case(
                example=example,
                output=output,
                failure_type="missing_citation",
                failure_stage="drafting",
                expected={"must_include_citation": True},
                actual={"citations": output.citations},
                notes="Target did not include a citation for a citation-required example.",
            )
        )

    citation_support_passed, citation_support_actual = _citation_support_result(
        output=output,
        citation_required=reference.must_include_citation,
    )
    metrics.append(
        _passed_metric(
            "citation_support",
            {
                "citations_reference_retrieved_docs": True,
                "citation_required": reference.must_include_citation,
            },
            citation_support_actual,
            citation_support_passed,
        )
    )
    if not citation_support_passed:
        bad_cases.append(
            _bad_case(
                example=example,
                output=output,
                failure_type="unsupported_citation",
                failure_stage="drafting",
                expected={
                    "citations_reference_retrieved_docs": True,
                    "citation_required": reference.must_include_citation,
                },
                actual=citation_support_actual,
                notes="Target citations were missing, unknown, or unsupported by retrieved evidence.",
            )
        )

    claim_support_passed, claim_support_actual = _claim_support_result(example, output)
    metrics.append(
        EvalMetricResult(
            name="claim_support",
            passed=claim_support_passed,
            score=(
                None
                if claim_support_passed is None
                else 1.0 if claim_support_passed else 0.0
            ),
            expected={"claims": example.metadata.get("claims", [])},
            actual=claim_support_actual,
            notes=(
                "Reference does not define claim-level support expectations."
                if claim_support_passed is None
                else None
            ),
        )
    )
    if claim_support_passed is False:
        bad_cases.append(
            _bad_case(
                example=example,
                output=output,
                failure_type="claim_not_supported_by_citation",
                failure_stage="drafting",
                expected={"claims": example.metadata.get("claims", [])},
                actual=claim_support_actual,
                notes="At least one expected answer claim was not backed by a cited retrieved document.",
            )
        )

    review_passed = output.review_required == reference.should_trigger_review
    metrics.append(
        _passed_metric(
            "review_trigger_accuracy",
            reference.should_trigger_review,
            output.review_required,
            review_passed,
        )
    )
    if not review_passed:
        bad_cases.append(
            _bad_case(
                example=example,
                output=output,
                failure_type="wrong_review_trigger",
                failure_stage="review_routing",
                expected={"should_trigger_review": reference.should_trigger_review},
                actual={"review_required": output.review_required},
                notes="Target review behavior did not match the fixed reference.",
            )
        )

    answer = (output.answer or "").lower()
    forbidden_claims = [
        claim
        for claim in reference.must_not_claim
        if claim.lower() in answer
    ]
    unsupported_claim_passed = not forbidden_claims
    metrics.append(
        _passed_metric(
            "unsupported_claim_absent",
            {"must_not_claim": reference.must_not_claim},
            {"forbidden_claims_present": forbidden_claims},
            unsupported_claim_passed,
        )
    )
    if not unsupported_claim_passed:
        bad_cases.append(
            _bad_case(
                example=example,
                output=output,
                failure_type="unsupported_claim_present",
                failure_stage="drafting",
                expected={"must_not_claim": reference.must_not_claim},
                actual={"forbidden_claims_present": forbidden_claims},
                notes="Target answer included a phrase that the reference forbids.",
            )
        )

    if reference.expected_status is not None:
        status_passed = output.status == reference.expected_status
        metrics.append(
            _passed_metric(
                "expected_status",
                reference.expected_status,
                output.status,
                status_passed,
            )
        )
        if not status_passed:
            bad_cases.append(
                _bad_case(
                    example=example,
                    output=output,
                    failure_type="wrong_status",
                    failure_stage="finalization",
                    expected={"expected_status": reference.expected_status},
                    actual={"status": output.status},
                    notes="Target ended in a different workflow status than expected.",
                )
            )
    else:
        metrics.append(
            EvalMetricResult(
                name="expected_status",
                passed=None,
                score=None,
                expected=None,
                actual=output.status,
                notes="Reference does not specify an expected status.",
            )
        )

    if reference.expected_risk_flags:
        actual_risk_flags = output.metadata.get("risk_flags")
        if isinstance(actual_risk_flags, list):
            missing_flags = sorted(set(reference.expected_risk_flags) - set(actual_risk_flags))
            risk_flags_passed = not missing_flags
            metrics.append(
                _passed_metric(
                    "expected_risk_flags",
                    reference.expected_risk_flags,
                    actual_risk_flags,
                    risk_flags_passed,
                )
            )
            if not risk_flags_passed:
                bad_cases.append(
                    _bad_case(
                        example=example,
                        output=output,
                        failure_type="missing_expected_risk_flag",
                        failure_stage="policy",
                        expected={"expected_risk_flags": reference.expected_risk_flags},
                        actual={"risk_flags": actual_risk_flags, "missing": missing_flags},
                        notes="Target risk assessment did not include all expected risk flags.",
                    )
                )
        else:
            metrics.append(
                EvalMetricResult(
                    name="expected_risk_flags",
                    passed=None,
                    score=None,
                    expected=reference.expected_risk_flags,
                    actual=None,
                    notes="Target does not expose risk flags.",
                )
            )
    else:
        metrics.append(
            EvalMetricResult(
                name="expected_risk_flags",
                passed=None,
                score=None,
                expected=[],
                actual=output.metadata.get("risk_flags"),
                notes="Reference does not specify expected risk flags.",
            )
        )

    if reference.expected_policy_ids:
        actual_policy_ids = output.metadata.get("failed_policy_ids")
        if isinstance(actual_policy_ids, list):
            missing_policy_ids = sorted(
                set(reference.expected_policy_ids) - set(actual_policy_ids)
            )
            policy_ids_passed = not missing_policy_ids
            metrics.append(
                _passed_metric(
                    "expected_policy_ids",
                    reference.expected_policy_ids,
                    actual_policy_ids,
                    policy_ids_passed,
                )
            )
            if not policy_ids_passed:
                bad_cases.append(
                    _bad_case(
                        example=example,
                        output=output,
                        failure_type="missing_expected_policy_id",
                        failure_stage="policy",
                        expected={"expected_policy_ids": reference.expected_policy_ids},
                        actual={
                            "failed_policy_ids": actual_policy_ids,
                            "missing": missing_policy_ids,
                        },
                        notes="Target policy assessment did not include all expected policy IDs.",
                    )
                )
        else:
            metrics.append(
                EvalMetricResult(
                    name="expected_policy_ids",
                    passed=None,
                    score=None,
                    expected=reference.expected_policy_ids,
                    actual=None,
                    notes="Target does not expose failed policy IDs.",
                )
            )
    else:
        metrics.append(
            EvalMetricResult(
                name="expected_policy_ids",
                passed=None,
                score=None,
                expected=[],
                actual=output.metadata.get("failed_policy_ids"),
                notes="Reference does not specify expected policy IDs.",
            )
        )

    if reference.expected_action_types:
        actual_action_types = output.metadata.get("proposed_action_types")
        if isinstance(actual_action_types, list):
            missing_action_types = sorted(
                set(reference.expected_action_types) - set(actual_action_types)
            )
            action_types_passed = not missing_action_types
            metrics.append(
                _passed_metric(
                    "expected_action_types",
                    reference.expected_action_types,
                    actual_action_types,
                    action_types_passed,
                )
            )
            if not action_types_passed:
                bad_cases.append(
                    _bad_case(
                        example=example,
                        output=output,
                        failure_type="missing_expected_action_type",
                        failure_stage="actions",
                        expected={"expected_action_types": reference.expected_action_types},
                        actual={
                            "proposed_action_types": actual_action_types,
                            "missing": missing_action_types,
                        },
                        notes="Target did not propose all expected support action types.",
                    )
                )
        else:
            metrics.append(
                EvalMetricResult(
                    name="expected_action_types",
                    passed=None,
                    score=None,
                    expected=reference.expected_action_types,
                    actual=None,
                    notes="Target does not expose proposed action types.",
                )
            )
    else:
        metrics.append(
            EvalMetricResult(
                name="expected_action_types",
                passed=None,
                score=None,
                expected=[],
                actual=output.metadata.get("proposed_action_types"),
                notes="Reference does not specify expected action types.",
            )
        )

    if reference.expected_action_statuses:
        actual_statuses_by_type = output.metadata.get("action_statuses_by_type")
        if isinstance(actual_statuses_by_type, dict):
            missing_statuses: dict[str, str] = {}
            for action_type, expected_status in reference.expected_action_statuses.items():
                actual_statuses = actual_statuses_by_type.get(action_type)
                if not isinstance(actual_statuses, list) or expected_status not in actual_statuses:
                    missing_statuses[action_type] = expected_status
            action_statuses_passed = not missing_statuses
            metrics.append(
                _passed_metric(
                    "expected_action_statuses",
                    reference.expected_action_statuses,
                    actual_statuses_by_type,
                    action_statuses_passed,
                )
            )
            if not action_statuses_passed:
                bad_cases.append(
                    _bad_case(
                        example=example,
                        output=output,
                        failure_type="wrong_action_status",
                        failure_stage="actions",
                        expected={"expected_action_statuses": reference.expected_action_statuses},
                        actual={
                            "action_statuses_by_type": actual_statuses_by_type,
                            "missing": missing_statuses,
                        },
                        notes="Target support action statuses did not match the fixed reference.",
                    )
                )
        else:
            metrics.append(
                EvalMetricResult(
                    name="expected_action_statuses",
                    passed=None,
                    score=None,
                    expected=reference.expected_action_statuses,
                    actual=None,
                    notes="Target does not expose action statuses by type.",
                )
            )
    else:
        metrics.append(
            EvalMetricResult(
                name="expected_action_statuses",
                passed=None,
                score=None,
                expected={},
                actual=output.metadata.get("action_statuses_by_type"),
                notes="Reference does not specify expected action statuses.",
            )
        )

    if reference.expected_failure_stage is not None:
        actual_failure_stages = sorted({bad_case.failure_stage for bad_case in bad_cases})
        failure_stage_passed = reference.expected_failure_stage in actual_failure_stages
        metrics.append(
            _passed_metric(
                "expected_failure_stage",
                reference.expected_failure_stage,
                actual_failure_stages,
                failure_stage_passed,
            )
        )
        if not failure_stage_passed:
            bad_cases.append(
                _bad_case(
                    example=example,
                    output=output,
                    failure_type="expected_failure_stage_missing",
                    failure_stage=reference.expected_failure_stage,
                    expected={"expected_failure_stage": reference.expected_failure_stage},
                    actual={"failure_stages": actual_failure_stages},
                    notes="Target failures did not include the expected workflow stage.",
                )
            )
    else:
        metrics.append(
            EvalMetricResult(
                name="expected_failure_stage",
                passed=None,
                score=None,
                expected=None,
                actual=sorted({bad_case.failure_stage for bad_case in bad_cases}),
                notes="Reference does not specify an expected failure stage.",
            )
        )

    primitive_passes = [
        metric.passed
        for metric in metrics
        if metric.name != "final_pass"
        and metric.passed is not None
    ]
    final_pass = all(primitive_passes)
    metrics.append(
        EvalMetricResult(
            name="final_pass",
            passed=final_pass,
            score=1.0 if final_pass else 0.0,
            expected="all supported primitive metrics pass",
            actual={"passed": primitive_passes},
            notes="Composite metric; not emitted as a separate bad case.",
        )
    )

    return EvalExampleResult(
        example_id=example.id,
        target=output.target,
        output=output,
        metrics=metrics,
        final_pass=final_pass,
        bad_cases=bad_cases,
    )


def _rate(results: list[EvalExampleResult], metric_name: str) -> float:
    metric_values = [
        metric.score
        for result in results
        for metric in result.metrics
        if metric.name == metric_name and metric.score is not None
    ]
    if not metric_values:
        return 0.0
    return round(sum(metric_values) / len(metric_values), 4)


def _optional_rate(results: list[EvalExampleResult], metric_name: str) -> float | None:
    metric_values = [
        metric.score
        for result in results
        for metric in result.metrics
        if metric.name == metric_name and metric.score is not None
    ]
    if not metric_values:
        return None
    return round(sum(metric_values) / len(metric_values), 4)


def summarize_results(
    *,
    run_id: str,
    dataset_name: str,
    target: str,
    results: list[EvalExampleResult],
    trace_events_path: str,
) -> EvalRunSummary:
    category_supported = any(result.output.category_supported for result in results)
    bad_case_count = sum(len(result.bad_cases) for result in results)
    return EvalRunSummary(
        run_id=run_id,
        dataset=dataset_name,
        target=target,  # type: ignore[arg-type]
        num_examples=len(results),
        category_supported=category_supported,
        category_accuracy=_rate(results, "category_accuracy") if category_supported else None,
        retrieval_hit_rate=_rate(results, "retrieval_hit"),
        citation_coverage=_rate(results, "citation_coverage"),
        citation_support_rate=_rate(results, "citation_support"),
        claim_support_rate=_optional_rate(results, "claim_support"),
        review_trigger_accuracy=_rate(results, "review_trigger_accuracy"),
        unsupported_claim_absence=_rate(results, "unsupported_claim_absent"),
        expected_status_accuracy=_optional_rate(results, "expected_status"),
        expected_risk_flag_accuracy=_optional_rate(results, "expected_risk_flags"),
        expected_policy_accuracy=_optional_rate(results, "expected_policy_ids"),
        expected_action_type_accuracy=_optional_rate(results, "expected_action_types"),
        expected_action_status_accuracy=_optional_rate(results, "expected_action_statuses"),
        expected_failure_stage_accuracy=_optional_rate(results, "expected_failure_stage"),
        final_pass_rate=_rate(results, "final_pass"),
        bad_case_count=bad_case_count,
        trace_events_path=trace_events_path,
    )

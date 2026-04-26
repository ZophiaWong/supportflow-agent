from app.evals.schemas import (
    BadCaseRecord,
    EvalExample,
    EvalExampleResult,
    EvalMetricResult,
    EvalRunSummary,
    EvalTargetOutput,
)


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
    expected: dict[str, object],
    actual: dict[str, object],
    notes: str,
) -> BadCaseRecord:
    return BadCaseRecord(
        example_id=example.id,
        target=output.target,
        failure_type=failure_type,
        expected=expected,
        actual=actual,
        trace_url=output.trace_url,
        notes=notes,
    )


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
    retrieval_passed = bool(retrieved_expected & retrieved_actual)
    metrics.append(
        _passed_metric(
            "retrieval_hit",
            reference.should_retrieve_doc_ids,
            output.retrieved_doc_ids,
            retrieval_passed,
        )
    )
    if not retrieval_passed:
        bad_cases.append(
            _bad_case(
                example=example,
                output=output,
                failure_type="missing_expected_retrieval",
                expected={"should_retrieve_doc_ids": reference.should_retrieve_doc_ids},
                actual={"retrieved_doc_ids": output.retrieved_doc_ids},
                notes="Target did not retrieve any expected KB document.",
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
                expected={"must_include_citation": True},
                actual={"citations": output.citations},
                notes="Target did not include a citation for a citation-required example.",
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
                expected={"should_trigger_review": reference.should_trigger_review},
                actual={"review_required": output.review_required},
                notes="Target review behavior did not match the fixed reference.",
            )
        )

    primitive_passes = [
        metric.passed
        for metric in metrics
        if metric.name
        in {"category_accuracy", "retrieval_hit", "citation_coverage", "review_trigger_accuracy"}
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
        review_trigger_accuracy=_rate(results, "review_trigger_accuracy"),
        final_pass_rate=_rate(results, "final_pass"),
        bad_case_count=bad_case_count,
        trace_events_path=trace_events_path,
    )

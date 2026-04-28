import type { PolicyAssessment } from "../lib/types";

interface PolicyAssessmentListProps {
  assessment?: PolicyAssessment | null;
}

function formatPolicyId(policyId: string): string {
  return policyId.replace(/_/g, " ");
}

export function PolicyAssessmentList({ assessment }: PolicyAssessmentListProps) {
  if (!assessment) {
    return <p>No policy assessment is available for this run.</p>;
  }

  const failedChecks = assessment.results.filter((result) => !result.passed);

  if (failedChecks.length === 0) {
    return <p>All policy checks passed.</p>;
  }

  return (
    <ul className="policy-list">
      {failedChecks.map((result) => (
        <li className="policy-list__item" key={result.policy_id}>
          <div className="policy-list__row">
            <strong>{formatPolicyId(result.policy_id)}</strong>
            <span className={`pill pill--policy-${result.severity}`}>{result.severity}</span>
          </div>
          <p>{result.message}</p>
          {result.evidence.length > 0 ? (
            <p className="draft-meta">Evidence: {result.evidence.join(", ")}</p>
          ) : null}
        </li>
      ))}
    </ul>
  );
}

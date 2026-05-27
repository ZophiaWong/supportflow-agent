import { Link, useSearchParams } from "react-router-dom";
import { useEffect, useState } from "react";

import { fetchPendingReviews } from "../lib/api";
import { formatRunLabel } from "../lib/runLabels";
import type { PendingReviewItem } from "../lib/types";

export function ReviewQueuePage() {
  const [searchParams] = useSearchParams();
  const [pendingReviews, setPendingReviews] = useState<PendingReviewItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadPendingReviews() {
      try {
        const items = await fetchPendingReviews();
        if (!cancelled) {
          setPendingReviews(items);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Unknown review queue error");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadPendingReviews();

    return () => {
      cancelled = true;
    };
  }, []);

  const blockedPolicyCount = pendingReviews.reduce(
    (count, item) => count + (item.policy_assessment?.failed_policy_ids.length ?? 0),
    0,
  );
  const proposedActionCount = pendingReviews.reduce(
    (count, item) => count + (item.proposed_actions ?? []).length,
    0,
  );
  const lowConfidenceCount = pendingReviews.filter((item) => item.draft.confidence < 0.85).length;
  const currentThreadId = searchParams.get("currentThreadId");

  return (
    <section className="screen">
      <div className="screen__header">
        <div>
          <p className="screen__eyebrow">Review queue</p>
          <h2>Pending reviews</h2>
          <p>Resolve paused runs by reviewing policy failures, actions, and draft quality.</p>
        </div>
        <span className="pill pill--workflow">{pendingReviews.length} pending</span>
      </div>

      {!loading && !error ? (
        <div className="metric-strip" aria-label="Review queue summary">
          <div className="metric-tile">
            <span>Waiting</span>
            <strong>{pendingReviews.length}</strong>
          </div>
          <div className="metric-tile">
            <span>Policy flags</span>
            <strong>{blockedPolicyCount}</strong>
          </div>
          <div className="metric-tile">
            <span>Proposed actions</span>
            <strong>{proposedActionCount}</strong>
          </div>
          <div className="metric-tile">
            <span>Low confidence</span>
            <strong>{lowConfidenceCount}</strong>
          </div>
        </div>
      ) : null}

      {loading ? <p className="status-panel">Loading pending reviews...</p> : null}
      {!loading && error ? <p className="status-panel status-panel--error">{error}</p> : null}
      {!loading && !error && pendingReviews.length === 0 ? (
        <p className="status-panel">No pending reviews right now.</p>
      ) : null}

      {!loading && !error && pendingReviews.length > 0 ? (
        <div className="data-table" role="table" aria-label="Pending reviews">
          <div className="data-table__row data-table__row--header" role="row">
            <span role="columnheader">Review case</span>
            <span role="columnheader">Category</span>
            <span role="columnheader">Priority</span>
            <span role="columnheader">Risk flags</span>
            <span role="columnheader">Policy checks</span>
            <span role="columnheader">Actions</span>
            <span role="columnheader">Confidence</span>
            <span role="columnheader">Action</span>
          </div>

          {pendingReviews.map((item) => (
            <div className="data-table__row" role="row" key={item.thread_id}>
              <span role="cell" data-label="Review case" className="data-table__primary">
                <span className="review-case-cell">
                  {formatRunLabel(item.ticket_id, item.thread_id)}
                  {currentThreadId === item.thread_id ? (
                    <span className="pill pill--workflow">Current</span>
                  ) : null}
                </span>
              </span>
              <span role="cell" data-label="Category">
                {item.classification.category}
              </span>
              <span role="cell" data-label="Priority">
                <span className="pill pill--workflow">{item.classification.priority}</span>
              </span>
              <span role="cell" data-label="Risk flags">
                {item.risk_flags.length > 0
                  ? item.risk_flags.map((flag) => flag.replace(/_/g, " ")).join(", ")
                  : "None"}
              </span>
              <span role="cell" data-label="Policy checks">
                {(item.policy_assessment?.failed_policy_ids ?? [])
                  .map((policyId) => policyId.replace(/_/g, " "))
                  .join(", ") || "None"}
              </span>
              <span role="cell" data-label="Actions">
                {(item.proposed_actions ?? [])
                  .map((action) => action.action_type.replace(/_/g, " "))
                  .join(", ") || "None"}
              </span>
              <span role="cell" data-label="Confidence">
                {item.draft.confidence.toFixed(2)}
              </span>
              <span role="cell" data-label="Action">
                <Link className="row-action" to={`/reviews/${item.thread_id}`}>
                  Review
                </Link>
              </span>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}

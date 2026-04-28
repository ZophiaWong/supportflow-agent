import { Link } from "react-router-dom";
import { useEffect, useState } from "react";

import { fetchPendingReviews } from "../lib/api";
import type { PendingReviewItem } from "../lib/types";

export function ReviewQueuePage() {
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

  return (
    <section className="screen">
      <div className="screen__header">
        <div>
          <p className="screen__eyebrow">Review Queue</p>
          <h2>Pending reviews</h2>
          <p>Open the next waiting review to approve, edit, or reject the AI draft.</p>
        </div>
        <span className="pill pill--workflow">{pendingReviews.length} pending</span>
      </div>

      {loading ? <p className="status-panel">Loading pending reviews...</p> : null}
      {!loading && error ? <p className="status-panel status-panel--error">{error}</p> : null}
      {!loading && !error && pendingReviews.length === 0 ? (
        <p className="status-panel">No pending reviews right now.</p>
      ) : null}

      {!loading && !error && pendingReviews.length > 0 ? (
        <div className="data-table" role="table" aria-label="Pending reviews">
          <div className="data-table__row data-table__row--header" role="row">
            <span role="columnheader">Ticket ID</span>
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
              <span role="cell" data-label="Ticket ID" className="data-table__primary">
                {item.ticket_id}
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
                  Open review
                </Link>
              </span>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}

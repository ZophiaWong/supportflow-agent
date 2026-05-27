import { Link } from "react-router-dom";

import { formatRunLabel } from "../lib/runLabels";
import type { RunStateResponse } from "../lib/types";

interface WorkflowRunSummaryProps {
  state: RunStateResponse | null;
  loading: boolean;
  error: string | null;
}

export function WorkflowRunSummary({ state, loading, error }: WorkflowRunSummaryProps) {
  if (error && !state) {
    return <section className="result-panel status-panel status-panel--error">{error}</section>;
  }

  if (!state) {
    return (
      <section className="result-panel result-panel--empty">
        <h2>Workflow runs</h2>
        <p>Start a workflow to create the current run for this ticket.</p>
      </section>
    );
  }

  return (
    <section className="result-panel">
      <div className="result-panel__header">
        <div>
          <p className="detail-panel__eyebrow">Workflow runs</p>
          <h2>{formatRunLabel(state.ticket_id, state.thread_id)}</h2>
        </div>
        <span className="pill pill--workflow">Current run</span>
      </div>

      {error ? (
        <div className="result-section">
          <h3>Polling error</h3>
          <p>{error}</p>
        </div>
      ) : null}

      <div className="detail-grid detail-grid--compact">
        <div>
          <dt>Status</dt>
          <dd>{state.status.replace(/_/g, " ")}</dd>
        </div>
        <div>
          <dt>Current node</dt>
          <dd>{state.current_node?.replace(/_/g, " ") ?? "pending"}</dd>
        </div>
        <div>
          <dt>Polling</dt>
          <dd>{loading ? "refreshing" : "idle"}</dd>
        </div>
      </div>

      {state.status === "waiting_review" ? (
        <Link className="row-action row-action--full" to={`/reviews/${state.thread_id}`}>
          Open review
        </Link>
      ) : null}
    </section>
  );
}

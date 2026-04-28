import type { RunStateResponse } from "../lib/types";
import { PolicyAssessmentList } from "./PolicyAssessmentList";
import { SupportActionList } from "./SupportActionList";

interface RunStatePanelProps {
  state: RunStateResponse | null;
  loading: boolean;
  error: string | null;
}

export function RunStatePanel({ state, loading, error }: RunStatePanelProps) {
  if (error && !state) {
    return <section className="result-panel status-panel status-panel--error">{error}</section>;
  }

  if (!state) {
    return (
      <section className="result-panel result-panel--empty">
        <h2>Run state</h2>
        <p>Start a workflow or reopen a saved thread to inspect the current graph state.</p>
      </section>
    );
  }

  return (
    <section className="result-panel" aria-live="polite">
      <div className="result-panel__header">
        <div>
          <p className="detail-panel__eyebrow">Current run state</p>
          <h2>Run {state.thread_id}</h2>
        </div>
        <span className="pill pill--workflow">{state.status}</span>
      </div>

      {error ? (
        <div className="result-section">
          <h3>Polling error</h3>
          <p>{error}</p>
        </div>
      ) : null}

      <div className="detail-grid">
        <div>
          <dt>Ticket</dt>
          <dd>{state.ticket_id}</dd>
        </div>
        <div>
          <dt>Current node</dt>
          <dd>{state.current_node ?? "unknown"}</dd>
        </div>
        <div>
          <dt>Polling</dt>
          <dd>{loading ? "refreshing" : "idle"}</dd>
        </div>
      </div>

      {state.classification ? (
        <div className="result-section">
          <h3>Classification</h3>
          <div className="result-tags">
            <span className="pill pill--workflow">{state.classification.category}</span>
            <span className="pill pill--workflow">{state.classification.priority}</span>
          </div>
          <p>{state.classification.reason}</p>
        </div>
      ) : null}

      {state.risk_assessment ? (
        <div className="result-section">
          <h3>Risk assessment</h3>
          <p>{state.risk_assessment.reason}</p>
          {state.risk_assessment.risk_flags.length > 0 ? (
            <div className="result-tags">
              {state.risk_assessment.risk_flags.map((flag) => (
                <span key={flag} className="pill pill--workflow">
                  {flag.replace(/_/g, " ")}
                </span>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}

      <div className="result-section">
        <h3>Policy checks</h3>
        <PolicyAssessmentList assessment={state.policy_assessment} />
      </div>

      {state.pending_review ? (
        <div className="result-section">
          <h3>Review status</h3>
          <p>This run is waiting for a human reviewer to approve, edit, or reject the draft.</p>
        </div>
      ) : null}

      <div className="result-section">
        <h3>Action ledger</h3>
        <SupportActionList actions={state.proposed_actions ?? []} />
      </div>

      {state.error ? (
        <div className="result-section">
          <h3>Error</h3>
          <p>{state.error}</p>
        </div>
      ) : null}
    </section>
  );
}

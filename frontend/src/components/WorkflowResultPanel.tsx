import type { RunTicketResponse } from "../lib/types";
import { SupportActionList } from "./SupportActionList";

interface WorkflowResultPanelProps {
  result: RunTicketResponse | null;
  error: string | null;
}

export function WorkflowResultPanel({ result, error }: WorkflowResultPanelProps) {
  if (error) {
    return (
      <section className="result-panel status-panel status-panel--error" aria-live="polite">
        {error}
      </section>
    );
  }

  if (!result) {
    return (
      <section className="result-panel result-panel--empty" aria-live="polite">
        <h2>Workflow output</h2>
        <p>Run the workflow for a selected ticket to see the classification, evidence, and draft reply.</p>
      </section>
    );
  }

  return (
    <section className="result-panel" aria-live="polite">
      <div className="result-panel__header">
        <div>
          <p className="detail-panel__eyebrow">Workflow status</p>
          <h2>Workflow output</h2>
        </div>
        <span className="pill pill--workflow">{result.status}</span>
      </div>

      <div className="result-section">
        <h3>Classification</h3>
        <div className="result-tags">
          <span className="pill pill--workflow">{result.classification.category}</span>
          <span className="pill pill--workflow">{result.classification.priority}</span>
        </div>
        <p>{result.classification.reason}</p>
      </div>

      <div className="result-section">
        <h3>Knowledge evidence</h3>
        <ul className="result-list">
          {result.retrieved_chunks.map((hit) => (
            <li key={hit.doc_id} className="result-list__item">
              <div className="result-list__row">
                <strong>{hit.title}</strong>
                <span>Score {hit.score.toFixed(2)}</span>
              </div>
              <p>{hit.snippet}</p>
            </li>
          ))}
        </ul>
      </div>

      {result.risk_assessment ? (
        <div className="result-section">
          <h3>Risk gate</h3>
          <p>{result.risk_assessment.reason}</p>
          {result.risk_assessment.risk_flags.length > 0 ? (
            <div className="result-tags">
              {result.risk_assessment.risk_flags.map((flag) => (
                <span key={flag} className="pill pill--workflow">
                  {flag.replace(/_/g, " ")}
                </span>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}

      <div className="result-section">
        <h3>Support actions</h3>
        <SupportActionList actions={result.proposed_actions ?? []} />
      </div>

      <div className="result-section">
        <h3>Draft reply</h3>
        <p className="draft-reply">{result.draft.answer}</p>
        <p className="draft-meta">
          Confidence {result.draft.confidence.toFixed(2)} | Citations:{" "}
          {result.draft.citations.length > 0 ? result.draft.citations.join(", ") : "None"}
        </p>
      </div>

      {result.status === "waiting_review" && result.pending_review ? (
        <div className="result-section">
          <h3>Human review required</h3>
          <p>
            This ticket is paused for reviewer action. Open the review queue to approve, edit, or
            reject the draft.
          </p>
          <p className="draft-meta">Thread {result.pending_review.thread_id}</p>
        </div>
      ) : null}

      {result.final_response ? (
        <div className="result-section">
          <h3>Final response</h3>
          <p className="draft-reply">{result.final_response.answer}</p>
          <p className="draft-meta">
            Disposition {result.final_response.disposition.replace(/_/g, " ")} | Citations:{" "}
            {result.final_response.citations.length > 0
              ? result.final_response.citations.join(", ")
              : "None"}
          </p>
        </div>
      ) : null}

      {result.status === "manual_takeover" ? (
        <div className="result-section">
          <h3>Manual takeover</h3>
          <p>A reviewer rejected the AI draft. A human agent must handle this ticket manually.</p>
        </div>
      ) : null}
    </section>
  );
}

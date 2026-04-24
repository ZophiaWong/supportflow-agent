import type { RunTicketResponse } from "../lib/types";

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

      <div className="result-section">
        <h3>Draft reply</h3>
        <p className="draft-reply">{result.draft.answer}</p>
        <p className="draft-meta">
          Confidence {result.draft.confidence.toFixed(2)} | Citations:{" "}
          {result.draft.citations.length > 0 ? result.draft.citations.join(", ") : "None"}
        </p>
      </div>
    </section>
  );
}

import type { RunTimelineEvent } from "../lib/types";

interface WorkflowTimelineProps {
  events: RunTimelineEvent[];
}

function formatEventLabel(eventType: RunTimelineEvent["event_type"]): string {
  return eventType.replace(/_/g, " ");
}

function formatTimestamp(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString();
}

export function WorkflowTimeline({ events }: WorkflowTimelineProps) {
  return (
    <section className="result-panel" aria-live="polite">
      <div className="result-panel__header">
        <div>
          <p className="detail-panel__eyebrow">Workflow timeline</p>
          <h2>Major steps</h2>
        </div>
        <span className="pill pill--workflow">{events.length} events</span>
      </div>

      {events.length === 0 ? (
        <p className="timeline-empty">Run a workflow to see timeline events.</p>
      ) : (
        <ol className="timeline-list">
          {events.map((event) => (
            <li key={event.event_id} className="timeline-item">
              <div className="timeline-item__header">
                <strong>{formatEventLabel(event.event_type)}</strong>
                <span className="pill pill--workflow">{event.status}</span>
              </div>
              <p className="timeline-item__meta">
                {event.node_name ? `Node ${event.node_name}` : "Run-level event"} |{" "}
                {formatTimestamp(event.created_at)}
              </p>
              {event.message ? <p className="timeline-item__message">{event.message}</p> : null}
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

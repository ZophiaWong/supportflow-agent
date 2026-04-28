import type { RunTraceEvent } from "../lib/types";

interface WorkflowTraceProps {
  events: RunTraceEvent[];
}

function formatNodeName(nodeName: string): string {
  return nodeName.replace(/_/g, " ");
}

function formatTimestamp(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString();
}

function stringListAttribute(
  attributes: Record<string, unknown>,
  key: string,
): string[] {
  const value = attributes[key];
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === "string");
}

function formatTraceToken(value: string): string {
  return value.replace(/_/g, " ");
}

function TraceAttributes({ event }: { event: RunTraceEvent }) {
  const failedPolicyIds = stringListAttribute(event.attributes, "failed_policy_ids");
  const proposedActionTypes = stringListAttribute(event.attributes, "proposed_action_types");
  const executedActionTypes = stringListAttribute(event.attributes, "executed_action_types");
  const finalDisposition =
    typeof event.attributes.final_disposition === "string"
      ? event.attributes.final_disposition
      : null;
  const reviewDecision =
    typeof event.attributes.review_decision === "string"
      ? event.attributes.review_decision
      : null;

  if (
    failedPolicyIds.length === 0 &&
    proposedActionTypes.length === 0 &&
    executedActionTypes.length === 0 &&
    !finalDisposition &&
    !reviewDecision
  ) {
    return null;
  }

  return (
    <div className="trace-attributes">
      {failedPolicyIds.length > 0 ? (
        <p>Policies: {failedPolicyIds.map(formatTraceToken).join(", ")}</p>
      ) : null}
      {proposedActionTypes.length > 0 ? (
        <p>Proposed actions: {proposedActionTypes.map(formatTraceToken).join(", ")}</p>
      ) : null}
      {executedActionTypes.length > 0 ? (
        <p>Executed actions: {executedActionTypes.map(formatTraceToken).join(", ")}</p>
      ) : null}
      {reviewDecision ? <p>Review decision: {formatTraceToken(reviewDecision)}</p> : null}
      {finalDisposition ? <p>Disposition: {formatTraceToken(finalDisposition)}</p> : null}
    </div>
  );
}

export function WorkflowTrace({ events }: WorkflowTraceProps) {
  return (
    <section className="result-panel" aria-live="polite">
      <div className="result-panel__header">
        <div>
          <p className="detail-panel__eyebrow">Run trace</p>
          <h2>Node spans</h2>
        </div>
        <span className="pill pill--workflow">{events.length} spans</span>
      </div>

      {events.length === 0 ? (
        <p className="timeline-empty">Run a workflow to see measured node spans.</p>
      ) : (
        <ol className="timeline-list">
          {events.map((event) => (
            <li key={event.trace_id} className="timeline-item">
              <div className="timeline-item__header">
                <strong>{formatNodeName(event.node_name)}</strong>
                <span className="pill pill--workflow">{event.status}</span>
              </div>
              <p className="timeline-item__meta">
                {event.duration_ms} ms | {formatTimestamp(event.started_at)}
              </p>
              <p className="timeline-item__message">{event.summary}</p>
              <TraceAttributes event={event} />
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

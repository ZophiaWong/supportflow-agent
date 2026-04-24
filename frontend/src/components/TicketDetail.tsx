import type { Ticket } from "../lib/types";

interface TicketDetailProps {
  ticket: Ticket;
  onRunWorkflow: () => void;
  runPending: boolean;
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

export function TicketDetail({ ticket, onRunWorkflow, runPending }: TicketDetailProps) {
  return (
    <section className="detail-panel" aria-labelledby="ticket-detail-title">
      <div className="detail-panel__header">
        <div>
          <p className="detail-panel__eyebrow">{ticket.customer_name}</p>
          <h2 id="ticket-detail-title">{ticket.subject}</h2>
        </div>
        <span className={`pill pill--${ticket.priority}`}>{ticket.priority}</span>
      </div>

      <dl className="detail-grid">
        <div>
          <dt>Status</dt>
          <dd>{ticket.status}</dd>
        </div>
        <div>
          <dt>Created</dt>
          <dd>{formatDate(ticket.created_at)}</dd>
        </div>
        <div>
          <dt>Ticket ID</dt>
          <dd>{ticket.id}</dd>
        </div>
      </dl>

      <div className="detail-panel__body">
        <h3>Customer summary</h3>
        <p>{ticket.preview ?? "No preview available for this ticket yet."}</p>
      </div>

      <button className="primary-button" type="button" onClick={onRunWorkflow} disabled={runPending}>
        {runPending ? "Running workflow..." : "Run workflow"}
      </button>
    </section>
  );
}

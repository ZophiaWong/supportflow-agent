import type { Ticket } from "../lib/types";

interface TicketListProps {
  tickets: Ticket[];
  selectedTicketId: string | null;
  onSelectTicket: (ticket: Ticket) => void;
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

export function TicketList({ tickets, selectedTicketId, onSelectTicket }: TicketListProps) {
  return (
    <div className="ticket-list" role="list" aria-label="Tickets">
      {tickets.map((ticket) => (
        <article
          className={`ticket-card ${selectedTicketId === ticket.id ? "ticket-card--selected" : ""}`}
          key={ticket.id}
          role="listitem"
        >
          <div className="ticket-card__header">
            <div>
              <p className="ticket-card__eyebrow">{ticket.customer_name}</p>
              <h2>{ticket.subject}</h2>
            </div>
            <span className={`pill pill--${ticket.priority}`}>{ticket.priority}</span>
          </div>
          <p className="ticket-card__preview">
            {ticket.preview ?? "No preview available for this ticket yet."}
          </p>
          <div className="ticket-card__meta">
            <span>Status: {ticket.status}</span>
            <span>Created: {formatDate(ticket.created_at)}</span>
            <span>ID: {ticket.id}</span>
          </div>
          <button
            className="ticket-card__action"
            type="button"
            onClick={() => onSelectTicket(ticket)}
          >
            {selectedTicketId === ticket.id ? "Selected" : "Open ticket"}
          </button>
        </article>
      ))}
    </div>
  );
}

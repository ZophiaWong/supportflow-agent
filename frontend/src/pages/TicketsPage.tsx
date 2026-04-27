import { Link } from "react-router-dom";
import { useEffect, useState } from "react";

import { fetchTickets } from "../lib/api";
import type { Ticket } from "../lib/types";

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

export function TicketsPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadTickets() {
      try {
        const nextTickets = await fetchTickets();
        if (!cancelled) {
          setTickets(nextTickets);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Unknown error");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadTickets();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="screen">
      <div className="screen__header">
        <div>
          <p className="screen__eyebrow">Inbox</p>
          <h2>Support tickets</h2>
          <p>Scan the queue, then open one ticket to run and inspect the workflow.</p>
        </div>
        <span className="pill pill--workflow">{tickets.length} tickets</span>
      </div>

      {loading ? <p className="status-panel">Loading tickets...</p> : null}
      {!loading && error ? <p className="status-panel status-panel--error">{error}</p> : null}
      {!loading && !error && tickets.length === 0 ? (
        <p className="status-panel">No tickets available.</p>
      ) : null}

      {!loading && !error && tickets.length > 0 ? (
        <div className="data-table" role="table" aria-label="Support tickets">
          <div className="data-table__row data-table__row--header" role="row">
            <span role="columnheader">Ticket ID</span>
            <span role="columnheader">Customer</span>
            <span role="columnheader">Subject</span>
            <span role="columnheader">Priority</span>
            <span role="columnheader">Status</span>
            <span role="columnheader">Created</span>
            <span role="columnheader">Action</span>
          </div>

          {tickets.map((ticket) => (
            <div className="data-table__row" role="row" key={ticket.id}>
              <span role="cell" data-label="Ticket ID">
                {ticket.id}
              </span>
              <span role="cell" data-label="Customer">
                {ticket.customer_name}
              </span>
              <span role="cell" data-label="Subject" className="data-table__primary">
                {ticket.subject}
              </span>
              <span role="cell" data-label="Priority">
                <span className={`pill pill--${ticket.priority}`}>{ticket.priority}</span>
              </span>
              <span role="cell" data-label="Status">
                {ticket.status}
              </span>
              <span role="cell" data-label="Created">
                {formatDate(ticket.created_at)}
              </span>
              <span role="cell" data-label="Action">
                <Link className="row-action" to={`/tickets/${ticket.id}`}>
                  Open ticket
                </Link>
              </span>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}

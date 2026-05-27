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

  const openCount = tickets.filter((ticket) => ticket.status === "open").length;
  const pendingCount = tickets.filter((ticket) => ticket.status === "pending").length;
  const priorityCount = tickets.filter((ticket) =>
    ticket.priority === "urgent" || ticket.priority === "high"
  ).length;

  return (
    <section className="screen">
      <div className="screen__header">
        <div>
          <p className="screen__eyebrow">Ticket queue</p>
          <h2>Support inbox</h2>
          <p>Prioritize customer requests, then open a ticket to run the AI workflow.</p>
        </div>
        <span className="pill pill--workflow">{tickets.length} tickets</span>
      </div>

      {!loading && !error ? (
        <div className="metric-strip" aria-label="Ticket queue summary">
          <div className="metric-tile">
            <span>Total</span>
            <strong>{tickets.length}</strong>
          </div>
          <div className="metric-tile">
            <span>Open</span>
            <strong>{openCount}</strong>
          </div>
          <div className="metric-tile">
            <span>High priority</span>
            <strong>{priorityCount}</strong>
          </div>
          <div className="metric-tile">
            <span>Pending</span>
            <strong>{pendingCount}</strong>
          </div>
        </div>
      ) : null}

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
                  Open
                </Link>
              </span>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}

import { useEffect, useState } from "react";

import { TicketList } from "../components/TicketList";
import { fetchTickets } from "../lib/api";
import type { Ticket } from "../lib/types";

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
    <main className="page-shell">
      <section className="hero">
        <p className="hero__kicker">Day 1 bootstrap</p>
        <h1>Support Inbox</h1>
        <p className="hero__lede">
          A minimal workflow shell that loads mock tickets from the FastAPI backend.
        </p>
      </section>

      {loading ? <p className="status-panel">Loading tickets...</p> : null}
      {!loading && error ? <p className="status-panel status-panel--error">{error}</p> : null}
      {!loading && !error && tickets.length === 0 ? (
        <p className="status-panel">No tickets available.</p>
      ) : null}
      {!loading && !error && tickets.length > 0 ? <TicketList tickets={tickets} /> : null}
    </main>
  );
}

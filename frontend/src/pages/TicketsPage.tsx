import { useEffect, useState } from "react";

import { TicketList } from "../components/TicketList";
import { TicketDetail } from "../components/TicketDetail";
import { WorkflowResultPanel } from "../components/WorkflowResultPanel";
import { fetchTickets, runTicket } from "../lib/api";
import type { RunTicketResponse, Ticket } from "../lib/types";

export function TicketsPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null);
  const [workflowResult, setWorkflowResult] = useState<RunTicketResponse | null>(null);
  const [workflowPending, setWorkflowPending] = useState(false);
  const [workflowError, setWorkflowError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadTickets() {
      try {
        const nextTickets = await fetchTickets();
        if (!cancelled) {
          setTickets(nextTickets);
          setSelectedTicketId((current) => current ?? nextTickets[0]?.id ?? null);
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

  const selectedTicket = tickets.find((ticket) => ticket.id === selectedTicketId) ?? null;

  async function handleRunWorkflow() {
    if (!selectedTicket) {
      return;
    }

    setWorkflowPending(true);
    setWorkflowError(null);

    try {
      const result = await runTicket(selectedTicket.id);
      setWorkflowResult(result);
    } catch (err) {
      setWorkflowError(err instanceof Error ? err.message : "Unknown workflow error");
      setWorkflowResult(null);
    } finally {
      setWorkflowPending(false);
    }
  }

  return (
    <main className="page-shell">
      <section className="hero">
        <p className="hero__kicker">Day 2 graph happy path</p>
        <h1>Support Inbox</h1>
        <p className="hero__lede">
          Select a ticket, run the LangGraph workflow, and inspect the classification,
          retrieved knowledge, and draft reply.
        </p>
      </section>

      {loading ? <p className="status-panel">Loading tickets...</p> : null}
      {!loading && error ? <p className="status-panel status-panel--error">{error}</p> : null}
      {!loading && !error && tickets.length === 0 ? (
        <p className="status-panel">No tickets available.</p>
      ) : null}
      {!loading && !error && tickets.length > 0 ? (
        <section className="workspace">
          <div className="workspace__column">
            <h2 className="workspace__title">Tickets</h2>
            <TicketList
              tickets={tickets}
              selectedTicketId={selectedTicketId}
              onSelectTicket={(ticket) => {
                setSelectedTicketId(ticket.id);
                setWorkflowResult(null);
                setWorkflowError(null);
              }}
            />
          </div>

          <div className="workspace__column workspace__column--detail">
            <h2 className="workspace__title">Ticket detail</h2>
            {selectedTicket ? (
              <TicketDetail
                ticket={selectedTicket}
                onRunWorkflow={handleRunWorkflow}
                runPending={workflowPending}
              />
            ) : (
              <p className="status-panel">Select a ticket to see details.</p>
            )}

            <WorkflowResultPanel result={workflowResult} error={workflowError} />
          </div>
        </section>
      ) : null}
    </main>
  );
}

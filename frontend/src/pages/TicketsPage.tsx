import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { RunStatePanel } from "../components/RunStatePanel";
import { TicketList } from "../components/TicketList";
import { WorkflowTimeline } from "../components/WorkflowTimeline";
import { TicketDetail } from "../components/TicketDetail";
import { WorkflowResultPanel } from "../components/WorkflowResultPanel";
import { fetchRunState, fetchRunTimeline, fetchTickets, runTicket } from "../lib/api";
import type { RunStateResponse, RunTicketResponse, RunTimelineEvent, Ticket } from "../lib/types";

const LAST_THREAD_ID_STORAGE_KEY = "supportflow:last-thread-id";

function shouldPoll(status: RunStateResponse["status"] | RunTicketResponse["status"]): boolean {
  return status === "running" || status === "waiting_review";
}

export function TicketsPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null);
  const [workflowResult, setWorkflowResult] = useState<RunTicketResponse | null>(null);
  const [workflowPending, setWorkflowPending] = useState(false);
  const [workflowError, setWorkflowError] = useState<string | null>(null);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(() => {
    if (typeof window === "undefined") {
      return null;
    }

    return window.localStorage.getItem(LAST_THREAD_ID_STORAGE_KEY);
  });
  const [runState, setRunState] = useState<RunStateResponse | null>(null);
  const [timelineEvents, setTimelineEvents] = useState<RunTimelineEvent[]>([]);
  const [runStateLoading, setRunStateLoading] = useState(false);
  const [runStateError, setRunStateError] = useState<string | null>(null);
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

  useEffect(() => {
    if (!activeThreadId) {
      setRunState(null);
      setTimelineEvents([]);
      setRunStateError(null);
      return;
    }

    const threadId = activeThreadId;
    let cancelled = false;
    let timeoutId: number | null = null;

    async function loadRunInspection() {
      setRunStateLoading(true);
      try {
        const [nextState, nextTimeline] = await Promise.all([
          fetchRunState(threadId),
          fetchRunTimeline(threadId),
        ]);

        if (cancelled) {
          return;
        }

        setRunState(nextState);
        setTimelineEvents(nextTimeline.events);
        setRunStateError(null);
        setSelectedTicketId((current) => current ?? nextState.ticket_id);

        if (shouldPoll(nextState.status)) {
          timeoutId = window.setTimeout(() => {
            void loadRunInspection();
          }, 1500);
        }
      } catch (err) {
        if (!cancelled) {
          setRunStateError(err instanceof Error ? err.message : "Unknown run state error");
        }
      } finally {
        if (!cancelled) {
          setRunStateLoading(false);
        }
      }
    }

    void loadRunInspection();

    return () => {
      cancelled = true;
      if (timeoutId !== null) {
        window.clearTimeout(timeoutId);
      }
    };
  }, [activeThreadId]);

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
      setActiveThreadId(result.thread_id);
      window.localStorage.setItem(LAST_THREAD_ID_STORAGE_KEY, result.thread_id);
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
        <p className="hero__kicker">Day 4 run timeline</p>
        <h1>Support Inbox</h1>
        <p className="hero__lede">
          Select a ticket, run the LangGraph workflow, and inspect both the business result and
          the Day 4 run timeline for the current `thread_id`.
        </p>
        <div className="hero__nav">
          <Link className="secondary-link" to="/reviews">
            Open review queue
          </Link>
        </div>
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

          <div className="workspace__column workspace__column--timeline">
            <h2 className="workspace__title">Run inspection</h2>
            <RunStatePanel state={runState} loading={runStateLoading} error={runStateError} />
            <WorkflowTimeline events={timelineEvents} />
          </div>
        </section>
      ) : null}
    </main>
  );
}

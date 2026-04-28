import { Link, useParams } from "react-router-dom";
import { useEffect, useState } from "react";

import { RunStatePanel } from "../components/RunStatePanel";
import { TicketDetail } from "../components/TicketDetail";
import { WorkflowResultPanel } from "../components/WorkflowResultPanel";
import { WorkflowTimeline } from "../components/WorkflowTimeline";
import { WorkflowTrace } from "../components/WorkflowTrace";
import { fetchRunState, fetchRunTimeline, fetchRunTrace, fetchTickets, runTicket } from "../lib/api";
import type {
  RunStateResponse,
  RunTicketResponse,
  RunTimelineEvent,
  RunTraceEvent,
  Ticket,
} from "../lib/types";

const LAST_THREAD_ID_STORAGE_KEY = "supportflow:last-thread-id";

function shouldPoll(status: RunStateResponse["status"] | RunTicketResponse["status"]): boolean {
  return status === "running" || status === "waiting_review";
}

export function TicketDetailPage() {
  const { ticketId } = useParams<{ ticketId: string }>();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
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
  const [traceEvents, setTraceEvents] = useState<RunTraceEvent[]>([]);
  const [runStateLoading, setRunStateLoading] = useState(false);
  const [runStateError, setRunStateError] = useState<string | null>(null);

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

  useEffect(() => {
    if (!activeThreadId) {
      setRunState(null);
      setTimelineEvents([]);
      setTraceEvents([]);
      setRunStateError(null);
      return;
    }

    const threadId = activeThreadId;
    let cancelled = false;
    let timeoutId: number | null = null;

    async function loadRunInspection() {
      setRunStateLoading(true);
      try {
        const [nextState, nextTimeline, nextTrace] = await Promise.all([
          fetchRunState(threadId),
          fetchRunTimeline(threadId),
          fetchRunTrace(threadId),
        ]);

        if (cancelled) {
          return;
        }

        setRunState(nextState.ticket_id === ticketId ? nextState : null);
        setTimelineEvents(nextState.ticket_id === ticketId ? nextTimeline.events : []);
        setTraceEvents(nextState.ticket_id === ticketId ? nextTrace.events : []);
        setRunStateError(null);

        if (nextState.ticket_id === ticketId && shouldPoll(nextState.status)) {
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
  }, [activeThreadId, ticketId]);

  const ticket = tickets.find((item) => item.id === ticketId) ?? null;

  async function handleRunWorkflow() {
    if (!ticket) {
      return;
    }

    setWorkflowPending(true);
    setWorkflowError(null);

    try {
      const result = await runTicket(ticket.id);
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

  if (loading) {
    return <p className="status-panel">Loading ticket...</p>;
  }

  if (error) {
    return <p className="status-panel status-panel--error">{error}</p>;
  }

  if (!ticket) {
    return (
      <section className="screen">
        <div className="empty-state">
          <h2>Ticket not found</h2>
          <p>The ticket ID in this URL is not available in the current inbox.</p>
          <Link className="secondary-link" to="/tickets">
            Back to inbox
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className="screen">
      <div className="screen__header">
        <div>
          <p className="screen__eyebrow">Ticket detail</p>
          <h2>{ticket.id}</h2>
          <p>Inspect the customer request, run the workflow, and review the graph state.</p>
        </div>
        <Link className="secondary-link" to="/tickets">
          Back to inbox
        </Link>
      </div>

      <div className="detail-layout">
        <div className="detail-layout__primary">
          <TicketDetail
            ticket={ticket}
            onRunWorkflow={handleRunWorkflow}
            runPending={workflowPending}
          />
          <WorkflowResultPanel result={workflowResult} error={workflowError} />
        </div>

        <div className="detail-layout__inspection">
          <RunStatePanel state={runState} loading={runStateLoading} error={runStateError} />
          <WorkflowTimeline events={timelineEvents} />
          <WorkflowTrace events={traceEvents} />
        </div>
      </div>
    </section>
  );
}

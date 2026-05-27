import { Link, useParams } from "react-router-dom";
import { useEffect, useState } from "react";

import { RunDiagnostics } from "../components/RunDiagnostics";
import { TicketDetail } from "../components/TicketDetail";
import { WorkflowRunSummary } from "../components/WorkflowRunSummary";
import { WorkflowResultPanel } from "../components/WorkflowResultPanel";
import { fetchRunState, fetchRunTimeline, fetchRunTrace, fetchTickets, startRun } from "../lib/api";
import type {
  RunStateResponse,
  RunTicketResponse,
  RunTimelineEvent,
  RunTraceEvent,
  Ticket,
} from "../lib/types";

const LAST_THREAD_ID_STORAGE_KEY = "supportflow:last-thread-id";

function shouldPoll(status: RunStateResponse["status"] | RunTicketResponse["status"]): boolean {
  return status === "running";
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
    setWorkflowResult(null);
    setWorkflowError(null);
    setRunState(null);
    setTimelineEvents([]);
    setTraceEvents([]);
    setRunStateError(null);
  }, [ticketId]);

  useEffect(() => {
    if (!activeThreadId) {
      setRunState(null);
      setTimelineEvents([]);
      setTraceEvents([]);
      setWorkflowResult(null);
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

        const isCurrentTicketRun = nextState.ticket_id === ticketId;
        setRunState(isCurrentTicketRun ? nextState : null);
        setTimelineEvents(isCurrentTicketRun ? nextTimeline.events : []);
        setTraceEvents(isCurrentTicketRun ? nextTrace.events : []);
        if (!isCurrentTicketRun) {
          setWorkflowResult(null);
        }
        if (isCurrentTicketRun && nextState.classification && nextState.draft) {
          setWorkflowResult({
            thread_id: nextState.thread_id,
            ticket_id: nextState.ticket_id,
            status: nextState.status,
            classification: nextState.classification,
            retrieved_chunks: nextState.retrieved_chunks,
            draft: nextState.draft,
            risk_assessment: nextState.risk_assessment,
            policy_assessment: nextState.policy_assessment,
            pending_review: nextState.pending_review,
            final_response: nextState.final_response,
            proposed_actions: nextState.proposed_actions,
            executed_actions: nextState.executed_actions,
          });
        }
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
    setWorkflowResult(null);
    setRunStateError(null);

    try {
      const started = await startRun(ticket.id);
      setTimelineEvents([]);
      setTraceEvents([]);
      setRunState({
        thread_id: started.thread_id,
        ticket_id: started.ticket_id,
        status: started.status,
        current_node: null,
        classification: null,
        retrieved_chunks: [],
        draft: null,
        risk_assessment: null,
        policy_assessment: null,
        review_decision: null,
        final_response: null,
        pending_review: null,
        proposed_actions: [],
        executed_actions: [],
        error: null,
      });
      setActiveThreadId(started.thread_id);
      window.localStorage.setItem(LAST_THREAD_ID_STORAGE_KEY, started.thread_id);
    } catch (err) {
      setWorkflowError(err instanceof Error ? err.message : "Unknown workflow error");
      setWorkflowResult(null);
    } finally {
      setWorkflowPending(false);
    }
  }

  const runInProgress = workflowPending || runState?.status === "running";

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
          <p className="screen__eyebrow">Ticket workbench</p>
          <h2>{ticket.id}</h2>
          <p>Run the workflow, inspect evidence, and route risky drafts to human review.</p>
        </div>
        <Link className="secondary-link" to="/tickets">
          Back to inbox
        </Link>
      </div>

      {runState?.status === "waiting_review" && activeThreadId ? (
        <div className="review-callout">
          <div>
            <p className="screen__eyebrow">Human review required</p>
            <h3>Policy checks paused this run for approval.</h3>
            <p>Open the exact review case for this workflow run.</p>
          </div>
          <Link className="row-action" to={`/reviews/${activeThreadId}`}>
            Open review
          </Link>
        </div>
      ) : null}

      <div className="workbench-layout">
        <div className="workbench-layout__ticket">
          <TicketDetail
            ticket={ticket}
            onRunWorkflow={handleRunWorkflow}
            runPending={runInProgress}
          />
        </div>

        <div className="workbench-layout__main">
          <WorkflowResultPanel result={workflowResult} error={workflowError} />
        </div>

        <div className="workbench-layout__inspection">
          <WorkflowRunSummary state={runState} loading={runStateLoading} error={runStateError} />
          <RunDiagnostics
            state={runState}
            loading={runStateLoading}
            error={runStateError}
            timelineEvents={timelineEvents}
            traceEvents={traceEvents}
          />
        </div>
      </div>
    </section>
  );
}

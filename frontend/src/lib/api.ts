import type {
  PendingReviewItem,
  RunStateResponse,
  RunTicketResponse,
  RunTraceResponse,
  RunTimelineResponse,
  SubmitReviewDecisionRequest,
  Ticket,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function fetchTickets(): Promise<Ticket[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/tickets`);

  if (!response.ok) {
    throw new Error(`Unable to load tickets (${response.status})`);
  }

  return (await response.json()) as Ticket[];
}

export async function runTicket(ticketId: string): Promise<RunTicketResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/tickets/${ticketId}/run`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error(`Unable to run workflow (${response.status})`);
  }

  return (await response.json()) as RunTicketResponse;
}

export async function fetchPendingReviews(): Promise<PendingReviewItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/reviews/pending`);

  if (!response.ok) {
    throw new Error(`Unable to load pending reviews (${response.status})`);
  }

  return (await response.json()) as PendingReviewItem[];
}

export async function resumeRun(
  threadId: string,
  body: SubmitReviewDecisionRequest,
): Promise<RunTicketResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/runs/${threadId}/resume`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(`Unable to resume workflow (${response.status})`);
  }

  return (await response.json()) as RunTicketResponse;
}

export async function fetchRunState(threadId: string): Promise<RunStateResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/runs/${threadId}/state`);

  if (!response.ok) {
    throw new Error(`Unable to load run state (${response.status})`);
  }

  return (await response.json()) as RunStateResponse;
}

export async function fetchRunTimeline(threadId: string): Promise<RunTimelineResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/runs/${threadId}/timeline`);

  if (!response.ok) {
    throw new Error(`Unable to load run timeline (${response.status})`);
  }

  return (await response.json()) as RunTimelineResponse;
}

export async function fetchRunTrace(threadId: string): Promise<RunTraceResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/runs/${threadId}/trace`);

  if (!response.ok) {
    throw new Error(`Unable to load run trace (${response.status})`);
  }

  return (await response.json()) as RunTraceResponse;
}

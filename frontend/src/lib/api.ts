import type { RunTicketResponse, Ticket } from "./types";

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

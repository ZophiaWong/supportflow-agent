import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import { TicketsPage } from "./TicketsPage";

const { runTicketMock } = vi.hoisted(() => ({
  runTicketMock: vi.fn(),
}));
const { fetchRunStateMock, fetchRunTimelineMock } = vi.hoisted(() => ({
  fetchRunStateMock: vi.fn(),
  fetchRunTimelineMock: vi.fn(),
}));

vi.mock("../lib/api", () => ({
  fetchTickets: vi.fn().mockResolvedValue([
    {
      id: "ticket-1002",
      subject: "Unable to reset administrator password",
      customer_name: "Jordan Patel",
      status: "pending",
      priority: "urgent",
      created_at: "2026-04-16T10:05:00Z",
      preview: "We are locked out of the admin dashboard.",
    },
  ]),
  fetchRunState: fetchRunStateMock,
  fetchRunTimeline: fetchRunTimelineMock,
  runTicket: runTicketMock,
}));

describe("TicketsPage", () => {
  beforeEach(() => {
    window.localStorage.clear();
    runTicketMock.mockReset();
    fetchRunStateMock.mockReset();
    fetchRunTimelineMock.mockReset();
    runTicketMock.mockResolvedValue({
      thread_id: "ticket-ticket-1002-1234abcd",
      ticket_id: "ticket-1002",
      status: "done",
      classification: {
        category: "account",
        priority: "P0",
        reason: "Ticket mentions account access or password recovery.",
      },
      retrieved_chunks: [
        {
          doc_id: "account_unlock",
          title: "Account Unlock Guide",
          score: 0.75,
          snippet: "If an administrator is locked out after a password reset...",
        },
      ],
      draft: {
        answer: "Hi Jordan Patel,\n\nWe reviewed your request.",
        citations: ["account_unlock"],
        confidence: 0.82,
      },
      final_response: {
        answer: "Hi Jordan Patel,\n\nWe reviewed your request.",
        citations: ["account_unlock"],
        disposition: "auto_finalized",
      },
    });
    fetchRunStateMock.mockResolvedValue({
      thread_id: "ticket-ticket-1002-1234abcd",
      ticket_id: "ticket-1002",
      status: "done",
      current_node: "finalize_reply",
      classification: {
        category: "account",
        priority: "P0",
        reason: "Ticket mentions account access or password recovery.",
      },
      retrieved_chunks: [
        {
          doc_id: "account_unlock",
          title: "Account Unlock Guide",
          score: 0.75,
          snippet: "If an administrator is locked out after a password reset...",
        },
      ],
      draft: {
        answer: "Hi Jordan Patel,\n\nWe reviewed your request.",
        citations: ["account_unlock"],
        confidence: 0.82,
      },
      final_response: {
        answer: "Hi Jordan Patel,\n\nWe reviewed your request.",
        citations: ["account_unlock"],
        disposition: "auto_finalized",
      },
      pending_review: null,
      error: null,
    });
    fetchRunTimelineMock.mockResolvedValue({
      thread_id: "ticket-ticket-1002-1234abcd",
      events: [
        {
          event_id: "evt-1",
          thread_id: "ticket-ticket-1002-1234abcd",
          ticket_id: "ticket-1002",
          event_type: "run_started",
          node_name: null,
          status: "running",
          message: "Workflow run started.",
          created_at: "2026-04-25T15:00:00Z",
          payload: null,
        },
        {
          event_id: "evt-2",
          thread_id: "ticket-ticket-1002-1234abcd",
          ticket_id: "ticket-1002",
          event_type: "run_completed",
          node_name: "finalize_reply",
          status: "done",
          message: "Workflow completed.",
          created_at: "2026-04-25T15:00:01Z",
          payload: null,
        },
      ],
    });
  });

  it("shows the fetched tickets after loading", async () => {
    render(
      <MemoryRouter>
        <TicketsPage />
      </MemoryRouter>,
    );

    expect(screen.getByText("Loading tickets...")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Ticket detail" })).toBeInTheDocument();
    });

    expect(screen.getByRole("button", { name: "Run workflow" })).toBeInTheDocument();
  });

  it("runs the workflow for the selected ticket and shows the result", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <TicketsPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Run workflow" })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Run workflow" }));

    await waitFor(() => {
      expect(screen.getByText("Account Unlock Guide")).toBeInTheDocument();
    });

    expect(runTicketMock).toHaveBeenCalledWith("ticket-1002");
    expect(fetchRunStateMock).toHaveBeenCalledWith("ticket-ticket-1002-1234abcd");
    expect(fetchRunTimelineMock).toHaveBeenCalledWith("ticket-ticket-1002-1234abcd");
    expect(screen.getAllByText("account")).toHaveLength(2);
    expect(screen.getAllByText("P0")).toHaveLength(2);
    expect(screen.getByText(/Confidence 0.82/)).toBeInTheDocument();
    expect(screen.getByText("Current run state")).toBeInTheDocument();
    expect(screen.getByText("Major steps")).toBeInTheDocument();
  });

  it("shows a waiting review message when the backend pauses the run", async () => {
    const user = userEvent.setup();
    runTicketMock.mockResolvedValueOnce({
      thread_id: "ticket-ticket-1002-1234abcd",
      ticket_id: "ticket-1002",
      status: "waiting_review",
      classification: {
        category: "account",
        priority: "P0",
        reason: "Ticket mentions account access or password recovery.",
      },
      retrieved_chunks: [
        {
          doc_id: "account_unlock",
          title: "Account Unlock Guide",
          score: 0.75,
          snippet: "If an administrator is locked out after a password reset...",
        },
      ],
      draft: {
        answer: "Hi Jordan Patel,\n\nWe reviewed your request.",
        citations: ["account_unlock"],
        confidence: 0.78,
      },
      risk_assessment: {
        review_required: true,
        risk_flags: ["priority_requires_review", "sensitive_request"],
        reason: "Review required because one or more Day 3 risk rules matched.",
      },
      pending_review: {
        thread_id: "ticket-ticket-1002",
        ticket_id: "ticket-1002",
        classification: {
          category: "account",
          priority: "P0",
          reason: "Ticket mentions account access or password recovery.",
        },
        draft: {
          answer: "Hi Jordan Patel,\n\nWe reviewed your request.",
          citations: ["account_unlock"],
          confidence: 0.78,
        },
        retrieved_chunks: [
          {
            doc_id: "account_unlock",
            title: "Account Unlock Guide",
            score: 0.75,
            snippet: "If an administrator is locked out after a password reset...",
          },
        ],
        risk_flags: ["priority_requires_review", "sensitive_request"],
        allowed_decisions: ["approve", "edit", "reject"],
      },
    });
    fetchRunStateMock.mockResolvedValueOnce({
      thread_id: "ticket-ticket-1002-1234abcd",
      ticket_id: "ticket-1002",
      status: "waiting_review",
      current_node: "human_review_interrupt",
      classification: {
        category: "account",
        priority: "P0",
        reason: "Ticket mentions account access or password recovery.",
      },
      retrieved_chunks: [
        {
          doc_id: "account_unlock",
          title: "Account Unlock Guide",
          score: 0.75,
          snippet: "If an administrator is locked out after a password reset...",
        },
      ],
      draft: {
        answer: "Hi Jordan Patel,\n\nWe reviewed your request.",
        citations: ["account_unlock"],
        confidence: 0.78,
      },
      risk_assessment: {
        review_required: true,
        risk_flags: ["priority_requires_review", "sensitive_request"],
        reason: "Review required because one or more Day 3 risk rules matched.",
      },
      pending_review: {
        thread_id: "ticket-ticket-1002-1234abcd",
        ticket_id: "ticket-1002",
        classification: {
          category: "account",
          priority: "P0",
          reason: "Ticket mentions account access or password recovery.",
        },
        draft: {
          answer: "Hi Jordan Patel,\n\nWe reviewed your request.",
          citations: ["account_unlock"],
          confidence: 0.78,
        },
        retrieved_chunks: [
          {
            doc_id: "account_unlock",
            title: "Account Unlock Guide",
            score: 0.75,
            snippet: "If an administrator is locked out after a password reset...",
          },
        ],
        risk_flags: ["priority_requires_review", "sensitive_request"],
        allowed_decisions: ["approve", "edit", "reject"],
      },
      final_response: null,
      error: null,
    });
    fetchRunTimelineMock.mockResolvedValueOnce({
      thread_id: "ticket-ticket-1002-1234abcd",
      events: [
        {
          event_id: "evt-1",
          thread_id: "ticket-ticket-1002-1234abcd",
          ticket_id: "ticket-1002",
          event_type: "interrupt_created",
          node_name: "human_review_interrupt",
          status: "waiting_review",
          message: "Workflow is waiting for human review.",
          created_at: "2026-04-25T15:00:01Z",
          payload: null,
        },
      ],
    });

    render(
      <MemoryRouter>
        <TicketsPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Run workflow" })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Run workflow" }));

    await waitFor(() => {
      expect(screen.getByText("Human review required")).toBeInTheDocument();
    });

    expect(screen.getByText(/Open the review queue/)).toBeInTheDocument();
    expect(screen.getByText("Review status")).toBeInTheDocument();
    expect(screen.getByText("interrupt created")).toBeInTheDocument();
  });

  it("restores the last inspected thread from local storage on reload", async () => {
    window.localStorage.setItem("supportflow:last-thread-id", "ticket-ticket-1002-1234abcd");

    render(
      <MemoryRouter>
        <TicketsPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(fetchRunStateMock).toHaveBeenCalledWith("ticket-ticket-1002-1234abcd");
    });

    expect(fetchRunTimelineMock).toHaveBeenCalledWith("ticket-ticket-1002-1234abcd");
  });
});

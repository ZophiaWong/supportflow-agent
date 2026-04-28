import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi } from "vitest";

import { TicketDetailPage } from "./TicketDetailPage";
import { TicketsPage } from "./TicketsPage";

const { runTicketMock } = vi.hoisted(() => ({
  runTicketMock: vi.fn(),
}));
const { fetchTicketsMock, fetchRunStateMock, fetchRunTimelineMock, fetchRunTraceMock } = vi.hoisted(() => ({
  fetchTicketsMock: vi.fn(),
  fetchRunStateMock: vi.fn(),
  fetchRunTimelineMock: vi.fn(),
  fetchRunTraceMock: vi.fn(),
}));

vi.mock("../lib/api", () => ({
  fetchTickets: fetchTicketsMock,
  fetchRunState: fetchRunStateMock,
  fetchRunTimeline: fetchRunTimelineMock,
  fetchRunTrace: fetchRunTraceMock,
  runTicket: runTicketMock,
}));

const tickets = [
  {
    id: "ticket-1002",
    subject: "Unable to reset administrator password",
    customer_name: "Jordan Patel",
    status: "pending",
    priority: "urgent",
    created_at: "2026-04-16T10:05:00Z",
    preview: "We are locked out of the admin dashboard.",
  },
  {
    id: "ticket-1003",
    subject: "Question about product export",
    customer_name: "Morgan Lee",
    status: "open",
    priority: "low",
    created_at: "2026-04-17T11:00:00Z",
    preview: "Can I export a monthly product usage report?",
  },
];

const runResult = {
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
    confidence: 0.82,
  },
  pending_review: {
    thread_id: "ticket-ticket-1002-1234abcd",
    ticket_id: "ticket-1002",
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
    risk_flags: ["priority_requires_review"],
    proposed_actions: [
      {
        action_id: "act-send",
        thread_id: "ticket-ticket-1002-1234abcd",
        ticket_id: "ticket-1002",
        action_type: "send_customer_reply",
        status: "proposed",
        idempotency_key: "ticket-ticket-1002-1234abcd:ticket-1002:send_customer_reply",
        requires_review: true,
        reason: "Send the final approved support reply to the customer.",
        payload: {},
        created_at: "2026-04-28T02:00:00Z",
        updated_at: "2026-04-28T02:00:00Z",
      },
    ],
    allowed_decisions: ["approve", "edit", "reject"],
  },
  final_response: null,
  proposed_actions: [
    {
      action_id: "act-send",
      thread_id: "ticket-ticket-1002-1234abcd",
      ticket_id: "ticket-1002",
      action_type: "send_customer_reply",
      status: "proposed",
      idempotency_key: "ticket-ticket-1002-1234abcd:ticket-1002:send_customer_reply",
      requires_review: true,
      reason: "Send the final approved support reply to the customer.",
      payload: {},
      created_at: "2026-04-28T02:00:00Z",
      updated_at: "2026-04-28T02:00:00Z",
    },
  ],
  executed_actions: [],
};

describe("Tickets routes", () => {
  beforeEach(() => {
    window.localStorage.clear();
    fetchTicketsMock.mockReset();
    runTicketMock.mockReset();
    fetchRunStateMock.mockReset();
    fetchRunTimelineMock.mockReset();
    fetchRunTraceMock.mockReset();
    fetchTicketsMock.mockResolvedValue(tickets);
    runTicketMock.mockResolvedValue(runResult);
    fetchRunStateMock.mockResolvedValue({
      ...runResult,
      current_node: "human_review_interrupt",
      error: null,
    });
    fetchRunTimelineMock.mockResolvedValue({
      thread_id: "ticket-ticket-1002-1234abcd",
      events: [
        {
          event_id: "evt-1",
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
    fetchRunTraceMock.mockResolvedValue({
      thread_id: "ticket-ticket-1002-1234abcd",
      events: [
        {
          trace_id: "trace-risk",
          thread_id: "ticket-ticket-1002-1234abcd",
          ticket_id: "ticket-1002",
          node_name: "risk_gate",
          span_type: "graph_node",
          status: "completed",
          started_at: "2026-04-25T15:00:00Z",
          ended_at: "2026-04-25T15:00:00.003Z",
          duration_ms: 3,
          summary: "Policy evaluation found 2 failed checks.",
          attributes: {
            failed_policy_ids: [
              "priority_requires_review",
              "high_impact_action_requires_review",
            ],
            proposed_action_types: ["send_customer_reply"],
          },
        },
      ],
    });
  });

  it("shows a full-width inbox list with links to ticket detail routes", async () => {
    render(
      <MemoryRouter>
        <TicketsPage />
      </MemoryRouter>,
    );

    expect(screen.getByText("Loading tickets...")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByRole("table", { name: "Support tickets" })).toBeInTheDocument();
    });

    expect(screen.getByRole("columnheader", { name: "Ticket ID" })).toBeInTheDocument();
    expect(screen.getByText("Jordan Patel")).toBeInTheDocument();
    expect(screen.getByText("Unable to reset administrator password")).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "Open ticket" })[0]).toHaveAttribute(
      "href",
      "/tickets/ticket-1002",
    );
  });

  it("navigates from inbox list to a ticket detail route", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={["/tickets"]}>
        <Routes>
          <Route path="/tickets" element={<TicketsPage />} />
          <Route path="/tickets/:ticketId" element={<TicketDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getAllByRole("link", { name: "Open ticket" })[0]).toBeInTheDocument();
    });

    await user.click(screen.getAllByRole("link", { name: "Open ticket" })[0]);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Run workflow" })).toBeInTheDocument();
    });

    expect(screen.getByRole("heading", { name: "ticket-1002" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to inbox" })).toHaveAttribute("href", "/tickets");
  });

  it("runs the workflow on the ticket detail route and shows run inspection", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={["/tickets/ticket-1002"]}>
        <Routes>
          <Route path="/tickets/:ticketId" element={<TicketDetailPage />} />
        </Routes>
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
    expect(fetchRunTraceMock).toHaveBeenCalledWith("ticket-ticket-1002-1234abcd");
    expect(screen.getByText("Current run state")).toBeInTheDocument();
    expect(screen.getAllByText("send customer reply").length).toBeGreaterThan(0);
    expect(screen.getByText("Major steps")).toBeInTheDocument();
    expect(screen.getByText("Node spans")).toBeInTheDocument();
    expect(screen.getByText(/high impact action requires review/)).toBeInTheDocument();
  });

  it("restores the last inspected thread on a matching ticket detail route", async () => {
    window.localStorage.setItem("supportflow:last-thread-id", "ticket-ticket-1002-1234abcd");

    render(
      <MemoryRouter initialEntries={["/tickets/ticket-1002"]}>
        <Routes>
          <Route path="/tickets/:ticketId" element={<TicketDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(fetchRunStateMock).toHaveBeenCalledWith("ticket-ticket-1002-1234abcd");
    });

    expect(fetchRunTimelineMock).toHaveBeenCalledWith("ticket-ticket-1002-1234abcd");
    expect(fetchRunTraceMock).toHaveBeenCalledWith("ticket-ticket-1002-1234abcd");
  });

  it("shows a recoverable state for a missing ticket route", async () => {
    render(
      <MemoryRouter initialEntries={["/tickets/missing-ticket"]}>
        <Routes>
          <Route path="/tickets/:ticketId" element={<TicketDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Ticket not found" })).toBeInTheDocument();
    });

    expect(screen.getByRole("link", { name: "Back to inbox" })).toHaveAttribute("href", "/tickets");
  });
});

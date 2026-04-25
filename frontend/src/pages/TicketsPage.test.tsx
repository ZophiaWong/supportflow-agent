import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import { TicketsPage } from "./TicketsPage";

const { runTicketMock } = vi.hoisted(() => ({
  runTicketMock: vi.fn(),
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
  runTicket: runTicketMock,
}));

describe("TicketsPage", () => {
  beforeEach(() => {
    runTicketMock.mockReset();
    runTicketMock.mockResolvedValue({
      thread_id: "ticket-ticket-1002",
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
    expect(screen.getByText("account")).toBeInTheDocument();
    expect(screen.getByText("P0")).toBeInTheDocument();
    expect(screen.getByText(/Confidence 0.82/)).toBeInTheDocument();
  });

  it("shows a waiting review message when the backend pauses the run", async () => {
    const user = userEvent.setup();
    runTicketMock.mockResolvedValueOnce({
      thread_id: "ticket-ticket-1002",
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
  });
});

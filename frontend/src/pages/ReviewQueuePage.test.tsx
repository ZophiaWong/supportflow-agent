import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi } from "vitest";

import { ReviewDetailPage } from "./ReviewDetailPage";
import { ReviewQueuePage } from "./ReviewQueuePage";

const { fetchPendingReviewsMock, resumeRunMock } = vi.hoisted(() => ({
  fetchPendingReviewsMock: vi.fn(),
  resumeRunMock: vi.fn(),
}));

vi.mock("../lib/api", () => ({
  fetchPendingReviews: fetchPendingReviewsMock,
  resumeRun: resumeRunMock,
}));

const pendingReview = {
  thread_id: "ticket-ticket-1001",
  ticket_id: "ticket-1001",
  classification: {
    category: "billing",
    priority: "P1",
    reason: "Ticket mentions billing or duplicate-charge language.",
  },
  draft: {
    answer: "Hi Avery Chen,\n\nWe reviewed your request.",
    citations: ["refund_policy"],
    confidence: 0.82,
  },
  retrieved_chunks: [
    {
      doc_id: "refund_policy",
      title: "Refund Policy",
      score: 0.8,
      snippet: "Refunds are processed after verification.",
    },
  ],
  risk_flags: ["billing_sensitive"],
  proposed_actions: [
    {
      action_id: "act-send",
      thread_id: "ticket-ticket-1001",
      ticket_id: "ticket-1001",
      action_type: "send_customer_reply",
      status: "proposed",
      idempotency_key: "ticket-ticket-1001:ticket-1001:send_customer_reply",
      requires_review: true,
      reason: "Send the final approved support reply to the customer.",
      payload: {},
      created_at: "2026-04-28T02:00:00Z",
      updated_at: "2026-04-28T02:00:00Z",
    },
    {
      action_id: "act-refund",
      thread_id: "ticket-ticket-1001",
      ticket_id: "ticket-1001",
      action_type: "create_refund_case",
      status: "proposed",
      idempotency_key: "ticket-ticket-1001:ticket-1001:create_refund_case",
      requires_review: true,
      reason: "Open a refund review case for the duplicate-charge request.",
      payload: {},
      created_at: "2026-04-28T02:00:00Z",
      updated_at: "2026-04-28T02:00:00Z",
    },
  ],
  allowed_decisions: ["approve", "edit", "reject"],
};

describe("Review routes", () => {
  beforeEach(() => {
    fetchPendingReviewsMock.mockReset();
    resumeRunMock.mockReset();
    fetchPendingReviewsMock.mockResolvedValue([pendingReview]);
    resumeRunMock.mockResolvedValue({
      thread_id: "ticket-ticket-1001",
      ticket_id: "ticket-1001",
      status: "done",
      classification: pendingReview.classification,
      retrieved_chunks: pendingReview.retrieved_chunks,
      draft: pendingReview.draft,
      proposed_actions: pendingReview.proposed_actions.map((action) => ({
        ...action,
        status: "executed",
      })),
      executed_actions: pendingReview.proposed_actions.map((action) => ({
        ...action,
        status: "executed",
      })),
      final_response: {
        answer: "Hi Avery Chen,\n\nWe reviewed your request.",
        citations: ["refund_policy"],
        disposition: "approved",
      },
    });
  });

  it("shows a full-width pending review queue with links to review detail routes", async () => {
    render(
      <MemoryRouter>
        <ReviewQueuePage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("table", { name: "Pending reviews" })).toBeInTheDocument();
    });

    expect(screen.getByRole("columnheader", { name: "Risk flags" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Actions" })).toBeInTheDocument();
    expect(screen.getByText("ticket-1001")).toBeInTheDocument();
    expect(screen.getByText("billing sensitive")).toBeInTheDocument();
    expect(screen.getByText(/send customer reply/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open review" })).toHaveAttribute(
      "href",
      "/reviews/ticket-ticket-1001",
    );
  });

  it("navigates from review queue to a review detail route", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={["/reviews"]}>
        <Routes>
          <Route path="/reviews" element={<ReviewQueuePage />} />
          <Route path="/reviews/:threadId" element={<ReviewDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("link", { name: "Open review" })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("link", { name: "Open review" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Submit review" })).toBeInTheDocument();
    });

    expect(screen.getByRole("heading", { name: "ticket-1001" })).toBeInTheDocument();
    expect(screen.getByText("create refund case")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to review queue" })).toHaveAttribute(
      "href",
      "/reviews",
    );
  });

  it("submits a reviewer decision from the review detail route", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={["/reviews/ticket-ticket-1001"]}>
        <Routes>
          <Route path="/reviews/:threadId" element={<ReviewDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("Refund Policy")).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Submit review" }));

    await waitFor(() => {
      expect(resumeRunMock).toHaveBeenCalledWith("ticket-ticket-1001", {
        decision: "approve",
        reviewer_note: null,
        edited_answer: null,
      });
    });

    expect(screen.getByText("Completed review")).toBeInTheDocument();
    expect(screen.getByText(/Disposition approved/)).toBeInTheDocument();
  });

  it("shows a recoverable state for a missing review route", async () => {
    render(
      <MemoryRouter initialEntries={["/reviews/missing-thread"]}>
        <Routes>
          <Route path="/reviews/:threadId" element={<ReviewDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Review not found" })).toBeInTheDocument();
    });

    expect(screen.getByRole("link", { name: "Back to review queue" })).toHaveAttribute(
      "href",
      "/reviews",
    );
  });
});

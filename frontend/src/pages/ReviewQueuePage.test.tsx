import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import { ReviewQueuePage } from "./ReviewQueuePage";

const { fetchPendingReviewsMock, resumeRunMock } = vi.hoisted(() => ({
  fetchPendingReviewsMock: vi.fn(),
  resumeRunMock: vi.fn(),
}));

vi.mock("../lib/api", () => ({
  fetchPendingReviews: fetchPendingReviewsMock,
  resumeRun: resumeRunMock,
}));

describe("ReviewQueuePage", () => {
  beforeEach(() => {
    fetchPendingReviewsMock.mockReset();
    resumeRunMock.mockReset();

    fetchPendingReviewsMock.mockResolvedValue([
      {
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
        allowed_decisions: ["approve", "edit", "reject"],
      },
    ]);

    resumeRunMock.mockResolvedValue({
      thread_id: "ticket-ticket-1001",
      ticket_id: "ticket-1001",
      status: "done",
      classification: {
        category: "billing",
        priority: "P1",
        reason: "Ticket mentions billing or duplicate-charge language.",
      },
      retrieved_chunks: [
        {
          doc_id: "refund_policy",
          title: "Refund Policy",
          score: 0.8,
          snippet: "Refunds are processed after verification.",
        },
      ],
      draft: {
        answer: "Hi Avery Chen,\n\nWe reviewed your request.",
        citations: ["refund_policy"],
        confidence: 0.82,
      },
      final_response: {
        answer: "Hi Avery Chen,\n\nWe reviewed your request.",
        citations: ["refund_policy"],
        disposition: "approved",
      },
    });
  });

  it("loads pending reviews and submits a reviewer decision", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <ReviewQueuePage />
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
});

import { render, screen } from "@testing-library/react";

import { RunStatePanel } from "./RunStatePanel";

describe("RunStatePanel", () => {
  it("preserves the last loaded run state when a poll refresh fails", () => {
    render(
      <RunStatePanel
        state={{
          thread_id: "ticket-ticket-1002-1234abcd",
          ticket_id: "ticket-1002",
          status: "running",
          current_node: "classify_ticket",
          classification: null,
          retrieved_chunks: [],
          draft: null,
          final_response: null,
          pending_review: null,
          error: null,
        }}
        loading={false}
        error="Unable to load run state (503)"
      />,
    );

    expect(screen.getByRole("heading", { name: "Run ticket-ticket-1002-1234abcd" })).toBeInTheDocument();
    expect(screen.getByText("Polling error")).toBeInTheDocument();
    expect(screen.getByText("Unable to load run state (503)")).toBeInTheDocument();
    expect(screen.getByText("classify_ticket")).toBeInTheDocument();
    expect(screen.getByText("running")).toBeInTheDocument();
  });
});

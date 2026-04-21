import { render, screen } from "@testing-library/react";

import { TicketList } from "./TicketList";

describe("TicketList", () => {
  it("renders ticket details", () => {
    render(
      <TicketList
        tickets={[
          {
            id: "ticket-1001",
            subject: "Refund requested for duplicate charge",
            customer_name: "Avery Chen",
            status: "open",
            priority: "high",
            created_at: "2026-04-16T09:30:00Z",
            preview: "I noticed two charges on my card.",
          },
        ]}
      />,
    );

    expect(screen.getByText("Refund requested for duplicate charge")).toBeInTheDocument();
    expect(screen.getByText("Avery Chen")).toBeInTheDocument();
    expect(screen.getByText("high")).toBeInTheDocument();
    expect(screen.getByText(/Status: open/)).toBeInTheDocument();
  });
});

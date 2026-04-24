import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { TicketList } from "./TicketList";

describe("TicketList", () => {
  it("renders ticket details", () => {
    const onSelectTicket = vi.fn();

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
        selectedTicketId={null}
        onSelectTicket={onSelectTicket}
      />,
    );

    expect(screen.getByText("Refund requested for duplicate charge")).toBeInTheDocument();
    expect(screen.getByText("Avery Chen")).toBeInTheDocument();
    expect(screen.getByText("high")).toBeInTheDocument();
    expect(screen.getByText(/Status: open/)).toBeInTheDocument();
  });

  it("notifies when a ticket is selected", async () => {
    const user = userEvent.setup();
    const onSelectTicket = vi.fn();

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
        selectedTicketId={null}
        onSelectTicket={onSelectTicket}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Open ticket" }));

    expect(onSelectTicket).toHaveBeenCalledTimes(1);
    expect(onSelectTicket).toHaveBeenCalledWith(
      expect.objectContaining({ id: "ticket-1001" }),
    );
  });
});

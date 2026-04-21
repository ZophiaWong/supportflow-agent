import { render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { TicketsPage } from "./TicketsPage";

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
}));

describe("TicketsPage", () => {
  it("shows the fetched tickets after loading", async () => {
    render(<TicketsPage />);

    expect(screen.getByText("Loading tickets...")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Unable to reset administrator password")).toBeInTheDocument();
    });
  });
});

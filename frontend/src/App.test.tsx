import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import { AppRoutes } from "./App";

const { fetchTicketsMock, fetchPendingReviewsMock } = vi.hoisted(() => ({
  fetchTicketsMock: vi.fn(),
  fetchPendingReviewsMock: vi.fn(),
}));

vi.mock("./lib/api", () => ({
  fetchTickets: fetchTicketsMock,
  fetchPendingReviews: fetchPendingReviewsMock,
  fetchRunState: vi.fn(),
  fetchRunTimeline: vi.fn(),
  fetchRunTrace: vi.fn(),
  runTicket: vi.fn(),
  startRun: vi.fn(),
  resumeRun: vi.fn(),
}));

describe("AppRoutes", () => {
  beforeEach(() => {
    fetchTicketsMock.mockReset();
    fetchPendingReviewsMock.mockReset();
    fetchTicketsMock.mockResolvedValue([]);
    fetchPendingReviewsMock.mockResolvedValue([]);
  });

  it("renders the shared shell navigation around routed pages", async () => {
    render(
      <MemoryRouter initialEntries={["/tickets"]}>
        <AppRoutes />
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: "SupportFlow Workbench" })).toBeInTheDocument();
    expect(screen.getByText("AI support operations")).toBeInTheDocument();
    expect(screen.getByText(/Triage tickets/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Tickets" })).toHaveAttribute("href", "/tickets");
    expect(screen.getByRole("link", { name: "Reviews" })).toHaveAttribute("href", "/reviews");

    await waitFor(() => {
      expect(screen.getByText("No tickets available.")).toBeInTheDocument();
    });
  });
});

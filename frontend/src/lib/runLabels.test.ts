import { describe, expect, it } from "vitest";

import { formatRunLabel, getShortRunId } from "./runLabels";

describe("run label helpers", () => {
  it("formats a ticket-scoped workflow run label", () => {
    expect(formatRunLabel("ticket-1001", "ticket-ticket-1001-a1b2c3d4")).toBe(
      "ticket-1001 · Run a1b2c3d4",
    );
  });

  it("uses the last 8 characters as the short run id", () => {
    expect(getShortRunId("ticket-ticket-1001-a1b2c3d4")).toBe("a1b2c3d4");
  });
});

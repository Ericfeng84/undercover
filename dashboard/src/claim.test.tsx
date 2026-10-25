import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import {
  claimDetail,
  claimEvent,
  decision,
  handlers,
  jsonResponse,
  queueSummaries,
  routeFetch,
} from "../tests/fixtures";
import { App } from "./App";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

async function openClaim() {
  render(<App />);
  const row = await screen.findByRole("button", { name: /CLM-1001/ });
  fireEvent.click(row);
}

it("shows a decided claim in full", async () => {
  const detail = claimDetail({
    status: "decided",
    decision: decision({
      paid_amount: 250,
      paid_at: "2026-07-01T12:30:00Z",
    }),
    events: [
      claimEvent(1, "Decision", "Approved $250.00. The delay was covered."),
      claimEvent(2, "Payment", "Paid $250.00."),
    ],
  });
  vi.stubGlobal(
    "fetch",
    routeFetch({
      "/api/claims": () => jsonResponse(queueSummaries()),
      "/api/claims/CLM-1001": () => jsonResponse(detail),
      "/api/handlers": () => jsonResponse(handlers),
    }),
  );

  await openClaim();

  expect(await screen.findByText(/My flight home from Rome/)).toBeDefined();
  expect(screen.getByText("Airport hotel, one night")).toBeDefined();
  expect(screen.getByText("$245.00")).toBeDefined();
  expect(screen.getByText("Meridian Air cancellation notice")).toBeDefined();
  expect(
    screen.getByText(/Flight MA 611 was canceled because of crew availability/),
  ).toBeDefined();
  expect(screen.getByText("POL-2001")).toBeDefined();
  expect(screen.getByText("UnderCover Premium")).toBeDefined();
  expect(screen.getAllByText("Rome, Italy").length).toBeGreaterThan(0);
  expect(screen.getByText("CLM-0412")).toBeDefined();
  expect(
    screen.getByText("Checked bag arrived 30 hours late in Lisbon"),
  ).toBeDefined();
  expect(screen.getByRole("button", { name: "Back to queue" })).toBeDefined();
  expect(screen.getByText(/Approved\s+\$250\.00/)).toBeDefined();
  expect(screen.getByText("Eligible costs less the deductible.")).toBeDefined();
  expect(
    screen.getByText("The policy wording covers the delay."),
  ).toBeDefined();
  expect(screen.getByText("Section 3 and Section 10")).toBeDefined();
  expect(screen.getAllByText("Decision").length).toBeGreaterThan(0);
  expect(screen.getByText("Payment")).toBeDefined();
  expect(screen.getByText(/Paid \$250\.00 on/)).toBeDefined();
  expect(screen.queryByRole("button", { name: "Work this claim" })).toBeNull();
});

it("works a waiting claim and shows the steps arriving", async () => {
  const waiting = claimDetail();
  const inProgress = claimDetail({
    status: "in_progress",
    events: [
      claimEvent(
        1,
        "Read claim",
        "Read CLM-1001 for Maya Patel: trip delay, $420.00 claimed.",
      ),
    ],
  });
  const decided = claimDetail({
    status: "decided",
    decision: decision({
      paid_amount: 250,
      paid_at: "2026-07-01T12:30:00Z",
    }),
    events: [
      claimEvent(1, "Decision", "Approved $250.00."),
      claimEvent(2, "Payment", "Paid $250.00."),
    ],
  });

  let resolveWork: ((response: Response) => void) | undefined;
  const workResponse = new Promise<Response>((resolve) => {
    resolveWork = resolve;
  });
  let claimLoads = 0;

  vi.stubGlobal(
    "fetch",
    routeFetch({
      "/api/claims": () => jsonResponse(queueSummaries()),
      "/api/claims/CLM-1001": () => {
        claimLoads += 1;
        return jsonResponse(claimLoads === 1 ? waiting : inProgress);
      },
      "/api/claims/CLM-1001/work": () => workResponse,
      "/api/handlers": () => jsonResponse(handlers),
    }),
  );

  await openClaim();

  fireEvent.click(
    await screen.findByRole("button", { name: "Work this claim" }),
  );

  expect(await screen.findByText("In progress")).toBeDefined();
  expect(screen.queryByRole("button", { name: "Work this claim" })).toBeNull();

  expect(
    await screen.findByText("Read claim", {}, { timeout: 3000 }),
  ).toBeDefined();

  await act(async () => {
    resolveWork?.(jsonResponse(decided));
    await Promise.resolve();
  });

  expect(await screen.findByText(/Approved\s+\$250\.00/)).toBeDefined();
  expect(screen.getByText("Paid $250.00.")).toBeDefined();
  expect(await screen.findByText(/Paid \$250\.00 on/)).toBeDefined();
  expect(screen.queryByRole("button", { name: "Work this claim" })).toBeNull();
});

it("shows an error when the claim cannot be loaded", async () => {
  vi.stubGlobal(
    "fetch",
    routeFetch({
      "/api/claims": () => jsonResponse(queueSummaries()),
      "/api/claims/CLM-1001": () =>
        jsonResponse({ detail: "Claim unavailable" }, 500),
      "/api/handlers": () => jsonResponse(handlers),
    }),
  );

  await openClaim();

  const alert = await screen.findByRole("alert");
  expect(alert.textContent).toContain("Claim unavailable");
});

it("shows an error when the work request fails", async () => {
  vi.stubGlobal(
    "fetch",
    routeFetch({
      "/api/claims": () => jsonResponse(queueSummaries()),
      "/api/claims/CLM-1001": () => jsonResponse(claimDetail()),
      "/api/claims/CLM-1001/work": () =>
        jsonResponse({ detail: "The agent is unavailable" }, 500),
      "/api/handlers": () => jsonResponse(handlers),
    }),
  );

  await openClaim();
  fireEvent.click(
    await screen.findByRole("button", { name: "Work this claim" }),
  );

  const alert = await screen.findByRole("alert");
  expect(alert.textContent).toContain("The agent is unavailable");
  expect(
    await screen.findByRole("button", { name: "Work this claim" }),
  ).toBeDefined();
});

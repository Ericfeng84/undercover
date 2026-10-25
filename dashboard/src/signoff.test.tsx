import { cleanup, fireEvent, render, screen } from "@testing-library/react";
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
  fireEvent.click(await screen.findByRole("button", { name: /CLM-1001/ }));
}

function awaitingSignOffDetail() {
  return claimDetail({
    status: "awaiting_signoff",
    decision: decision({ payout: 1200 }),
    events: [claimEvent(1, "Decision", "Approved $1,200.00.")],
  });
}

it("shows a blocked payment and signs off with a handler", async () => {
  const signedOff = claimDetail({
    status: "decided",
    decision: decision({
      payout: 1200,
      signed_off_by: "HND-01",
      signed_off_at: "2026-07-01T13:00:00Z",
      paid_amount: 1200,
      paid_at: "2026-07-01T13:00:00Z",
    }),
    events: [
      claimEvent(1, "Decision", "Approved $1,200.00."),
      claimEvent(2, "Sign-off", "Signed off by Dana Whitfield."),
      claimEvent(3, "Payment released", "Paid $1,200.00."),
    ],
  });
  vi.stubGlobal(
    "fetch",
    routeFetch({
      "/api/claims": () => jsonResponse(queueSummaries()),
      "/api/claims/CLM-1001": () => jsonResponse(awaitingSignOffDetail()),
      "/api/claims/CLM-1001/sign-off": () => jsonResponse(signedOff),
      "/api/handlers": () => jsonResponse(handlers),
    }),
  );

  await openClaim();

  expect(
    await screen.findByRole("heading", { name: "Waiting for sign-off" }),
  ).toBeDefined();
  expect(screen.getAllByText("$1,200.00").length).toBeGreaterThan(0);
  expect(
    screen.getByText("The payment is blocked until a handler signs off."),
  ).toBeDefined();
  expect(screen.getByRole("option", { name: /Dana Whitfield/ })).toBeDefined();

  fireEvent.change(screen.getByLabelText("Handler"), {
    target: { value: "HND-01" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Sign off" }));

  expect(await screen.findByText("Decided")).toBeDefined();
  expect(await screen.findByText(/Paid \$1,200\.00 on/)).toBeDefined();
  expect(
    await screen.findByText(/Signed off by Dana Whitfield on/),
  ).toBeDefined();
  expect(screen.queryByRole("button", { name: "Sign off" })).toBeNull();
  expect(screen.queryByLabelText("Handler")).toBeNull();
});

it("shows an error when sign-off fails", async () => {
  vi.stubGlobal(
    "fetch",
    routeFetch({
      "/api/claims": () => jsonResponse(queueSummaries()),
      "/api/claims/CLM-1001": () => jsonResponse(awaitingSignOffDetail()),
      "/api/claims/CLM-1001/sign-off": () =>
        jsonResponse({ detail: "Sign-off failed" }, 500),
      "/api/handlers": () => jsonResponse(handlers),
    }),
  );

  await openClaim();
  fireEvent.click(await screen.findByRole("button", { name: "Sign off" }));

  const alert = await screen.findByRole("alert");
  expect(alert.textContent).toContain("Sign-off failed");
});

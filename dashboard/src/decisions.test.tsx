import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import {
  claimDetail,
  decision,
  handlers,
  jsonResponse,
  queueSummaries,
  routeFetch,
} from "../tests/fixtures";
import { App } from "./App";
import type { DecisionOutcome } from "./types";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

async function showDecidedClaim(outcome: DecisionOutcome) {
  const detail = claimDetail({
    status: "decided",
    decision: decision({ outcome, payout: 0 }),
  });
  vi.stubGlobal(
    "fetch",
    routeFetch({
      "/api/claims": () => jsonResponse(queueSummaries()),
      "/api/claims/CLM-1001": () => jsonResponse(detail),
      "/api/handlers": () => jsonResponse(handlers),
    }),
  );
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: /CLM-1001/ }));
  await screen.findByText("The policy wording covers the delay.");
}

it("shows a declined claim with no payment and no sign-off control", async () => {
  await showDecidedClaim("decline");

  expect(document.querySelector(".decision-outcome")?.textContent).toContain(
    "Declined",
  );
  expect(screen.getByText("No payment.")).toBeDefined();
  expect(screen.getByText("Section 3 and Section 10")).toBeDefined();
  expect(screen.queryByRole("button", { name: "Sign off" })).toBeNull();
  expect(screen.queryByLabelText("Handler")).toBeNull();
});

it("shows a referred claim with no payment and no sign-off control", async () => {
  await showDecidedClaim("refer");

  expect(document.querySelector(".decision-outcome")?.textContent).toContain(
    "Referred",
  );
  expect(screen.getByText("No payment.")).toBeDefined();
  expect(screen.getByText("Section 3 and Section 10")).toBeDefined();
  expect(screen.queryByRole("button", { name: "Sign off" })).toBeNull();
  expect(screen.queryByLabelText("Handler")).toBeNull();
});

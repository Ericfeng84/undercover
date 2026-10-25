import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { jsonResponse, queueSummaries, routeFetch } from "../tests/fixtures";
import { App } from "./App";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("lists the claims queue with the customer, type, amount and state", async () => {
  vi.stubGlobal(
    "fetch",
    routeFetch({ "/api/claims": () => jsonResponse(queueSummaries()) }),
  );

  render(<App />);

  expect(await screen.findByText("25 claims")).toBeDefined();
  expect(screen.getAllByText(/^CLM-\d{4}$/)).toHaveLength(25);
  expect(screen.getByText("Maya Patel")).toBeDefined();
  expect(screen.getAllByText("Trip delay")).toHaveLength(25);
  expect(screen.getAllByText("$420.00")).toHaveLength(25);
  expect(screen.getAllByText("Waiting")).toHaveLength(25);
});

it("shows an error when the queue cannot be loaded", async () => {
  vi.stubGlobal(
    "fetch",
    routeFetch({
      "/api/claims": () => jsonResponse({ detail: "Queue unavailable" }, 500),
    }),
  );

  render(<App />);

  const alert = await screen.findByRole("alert");
  expect(alert.textContent).toContain("Queue unavailable");
});

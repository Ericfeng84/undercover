import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import {
  jsonResponse,
  queueSummaries,
  routeFetch,
  textResponse,
} from "../tests/fixtures";
import { App } from "./App";

const INSTRUCTIONS =
  "# UnderCover Agent instructions\n\nDecide on the policy wording alone.";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("shows the read-only instructions from the API", async () => {
  vi.stubGlobal(
    "fetch",
    routeFetch({
      "/api/claims": () => jsonResponse(queueSummaries()),
      "/api/instructions": () => textResponse(INSTRUCTIONS),
    }),
  );

  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "Instructions" }));

  await screen.findByText(/Decide on the policy wording alone/);
  const instructions = document.querySelector("pre");
  expect(instructions?.textContent).toBe(INSTRUCTIONS);
  expect(screen.queryByRole("textbox")).toBeNull();
  expect(document.querySelector("textarea")).toBeNull();
  expect(document.querySelector("[contenteditable='true']")).toBeNull();
  expect(screen.queryByRole("button", { name: /save/i })).toBeNull();
});

it("shows an error when the instructions cannot be loaded", async () => {
  vi.stubGlobal(
    "fetch",
    routeFetch({
      "/api/claims": () => jsonResponse(queueSummaries()),
      "/api/instructions": () =>
        jsonResponse({ detail: "Instructions unavailable" }, 500),
    }),
  );

  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "Instructions" }));

  const alert = await screen.findByRole("alert");
  expect(alert.textContent).toContain("Instructions unavailable");
});

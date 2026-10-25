import { expect, it } from "vitest";
import { errorMessage, formatDateTime, formatMoney, humanize } from "./format";

it("formats money in US dollars", () => {
  expect(formatMoney(1250)).toBe("$1,250.00");
  expect(formatMoney(0)).toBe("$0.00");
});

it("turns identifiers into readable labels", () => {
  expect(humanize("trip_delay")).toBe("Trip delay");
  expect(humanize("electronics_plus")).toBe("Electronics plus");
});

it("formats a timestamp with its year", () => {
  expect(formatDateTime("2026-07-01T12:00:00Z")).toContain("2026");
});

it("reads an error message", () => {
  expect(errorMessage(new Error("Queue unavailable"))).toBe(
    "Queue unavailable",
  );
  expect(errorMessage("something else")).toBe("Something went wrong.");
});

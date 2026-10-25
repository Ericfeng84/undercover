import { expect, test } from "@playwright/test";

test("the queue lists every claim and opens CLM-1001", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("25 claims")).toBeVisible();
  await expect(page.locator(".queue-row")).toHaveCount(25);

  await page.getByRole("button", { name: /CLM-1001/ }).click();

  await expect(
    page.getByRole("heading", { name: "The customer's story" }),
  ).toBeVisible();
  await expect(page.getByText("Maya Patel").first()).toBeVisible();
  await expect(page.getByText(/My flight home from Rome/)).toBeVisible();
  await expect(
    page.getByText("Meridian Air cancellation notice"),
  ).toBeVisible();
  await expect(page.getByText("Hotel receipt")).toBeVisible();
});

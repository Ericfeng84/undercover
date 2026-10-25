import { expect, test } from "@playwright/test";

test("an over-limit approval waits for sign-off and then pays", async ({
  page,
  request,
}) => {
  const decision = await request.post(
    "http://127.0.0.1:8000/api/claims/CLM-1001/decision",
    {
      data: {
        outcome: "approve",
        payout: 1200,
        calculation: "Hotel, meals and taxis less the deductible.",
        reason:
          "The delay is covered under section 3 and the payout follows section 10.",
        policy_section: "Sections 3 and 10",
      },
    },
  );
  expect(decision.status()).toBe(200);

  await page.goto("/");
  await page.getByRole("button", { name: /CLM-1001/ }).click();

  await expect(
    page.getByRole("heading", { name: "Waiting for sign-off" }),
  ).toBeVisible();
  await expect(
    page.getByText("The payment is blocked until a handler signs off."),
  ).toBeVisible();
  await expect(page.getByText("$1,200.00").first()).toBeVisible();

  await page.locator("#handler-select").selectOption("HND-01");
  await page.getByRole("button", { name: "Sign off" }).click();

  await expect(page.locator(".status-decided")).toBeVisible();
  await expect(page.getByText(/Paid \$1,200\.00 on/)).toBeVisible();
  await expect(page.getByText(/Signed off by Dana Whitfield on/)).toBeVisible();

  const payment = await request.post(
    "http://127.0.0.1:8000/api/claims/CLM-1001/pay",
    { data: { amount: 1200 } },
  );
  expect(payment.status()).toBe(409);
});

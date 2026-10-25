import { expect, test } from "@playwright/test";

test("the instructions page is read only", async ({ page, request }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Instructions" }).click();

  const response = await request.get("http://127.0.0.1:8000/api/instructions");
  expect(response.ok()).toBeTruthy();
  const expected = await response.text();

  const instructions = page.locator("pre");
  await expect(instructions).toBeVisible();
  const actual = await instructions.evaluate((element) => element.textContent);
  expect(actual).toBe(expected);
  await expect(
    page.locator("input, textarea, [contenteditable='true']"),
  ).toHaveCount(0);
  await expect(page.getByRole("button", { name: /save/i })).toHaveCount(0);
});

import { test, expect } from "@playwright/test";
import { authenticateCitizen } from "./helpers";

test.describe("4.6 AI Assistant & RAG Verification", () => {
  test("Assistant page renders chat interface and dispatches inquiries", async ({ page }) => {
    await authenticateCitizen(page);
    await page.goto("/app/assistant");

    // 1. Verify chat interface components
    await expect(page.locator("button:has-text('New')").first()).toBeVisible({ timeout: 15000 });
    await expect(page.locator("text=Chats").or(page.locator("text=Inquiry History")).first()).toBeVisible();

    // 2. Verify input box exists
    const input = page.locator("textarea").first();
    await expect(input).toBeVisible();

    // 3. Send an inquiry
    await input.fill("What is the official procedure to correct a name in PAN card to match Aadhaar?");
    const sendButton = page.locator("button[type='submit']").filter({ hasText: /Send/i });
    await sendButton.click();

    // 4. Verify user message appears in chat
    await expect(page.locator("text=What is the official procedure to correct a name in PAN card")).toBeVisible({ timeout: 10000 });

    // 5. Response should arrive (either grounded RAG answer or graceful notice)
    await expect(
      page.locator("text=Statutory Notice").or(page.locator("text=Verified Statutory Sources")).or(page.locator("text=Precedents")).first()
    ).toBeVisible({ timeout: 25000 });
  });
});

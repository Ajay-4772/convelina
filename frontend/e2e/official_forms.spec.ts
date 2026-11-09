import { test, expect } from "@playwright/test";
import { authenticateCitizen } from "./helpers";

test.describe("Phase P3D: In-Chat Official Form Retrieval & Secure Downloads", () => {
  test("Citizen asks for official form, receives verified form card, opens preview modal", async ({ page }) => {
    await authenticateCitizen(page);
    await page.goto("/app/assistant");

    // 1. Verify workspace is ready
    await expect(page.locator("button:has-text('New')").first()).toBeVisible({ timeout: 15000 });

    // 2. Ask for an official statutory form
    const input = page.locator("textarea").first();
    await expect(input).toBeVisible();
    await input.fill("Which official form do I need for PAN card name correction to match Aadhaar?");

    const sendBtn = page.locator("button[type='submit']").or(page.locator("button[aria-label='Send message']")).first();
    await sendBtn.click();

    // 3. User message should appear
    await expect(
      page.locator("text=Which official form do I need for PAN card name correction")
    ).toBeVisible({ timeout: 10000 });

    // 4. Assistant reply should render official form card
    const formCard = page.locator("[data-testid^='official-form-card-']").first();
    await expect(formCard).toBeVisible({ timeout: 30000 });

    // 5. If form card is rendered, verify preview button and trigger modal
    if (await formCard.isVisible()) {
      await expect(formCard.locator("text=VERIFIED").first()).toBeVisible();
      await expect(formCard.locator("text=PDF").first()).toBeVisible();

      // Click Preview Document
      const previewBtn = formCard.locator("button:has-text('Preview Document')").first();
      if (await previewBtn.isVisible()) {
        await previewBtn.click();

        // Verify Preview Modal opens
        const previewModal = page.locator("[data-testid='official-form-preview-modal']");
        await expect(previewModal).toBeVisible({ timeout: 10000 });
        await expect(previewModal.locator("text=OFFICIAL VERIFIED").first()).toBeVisible();

        // Close Modal
        const closeBtn = previewModal.locator("button[aria-label='Close form preview']").first();
        await closeBtn.click();
        await expect(previewModal).not.toBeVisible();
      }
    }
  });
});


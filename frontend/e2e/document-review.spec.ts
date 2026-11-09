import { test, expect } from "@playwright/test";
import { authenticateCitizen, generateSyntheticPdfBuffer } from "./helpers";

test.describe("4.4 OCR Extraction & Stage 5 Field Review", () => {
  test("Citizen can review and correct extracted demographic attributes", async ({ page }) => {
    await authenticateCitizen(page);
    await page.goto("/app/inconsistencies");

    // 1. Upload a synthetic PAN credential
    const syntheticPanPdf = generateSyntheticPdfBuffer([
      "INCOME TAX DEPARTMENT - GOVT OF INDIA",
      "Permanent Account Number Card",
      "Name: VIKRAM MEHRA",
      "Father's Name: SURESH MEHRA",
      "DOB: 15/06/1990",
      "PAN: ABCDE1234F",
    ]);

    await page.locator("select").selectOption("pan");
    await page.setInputFiles('input[type="file"]', {
      name: "synthetic_pan.pdf",
      mimeType: "application/pdf",
      buffer: syntheticPanPdf,
    });

    // Wait for document to appear in the library
    await expect(page.locator("text=PAN Card").first()).toBeVisible({ timeout: 20000 });

    // 2. Click "Review Fields" / "Review Data" button
    const reviewBtn = page.locator("button").filter({ hasText: /Review (Fields|Data)/ }).first();
    await expect(reviewBtn).toBeVisible();
    await reviewBtn.click();

    // 3. Verify modal opens
    await expect(page.locator("h3:has-text('Review Extracted Demographic Fields')")).toBeVisible();
    await expect(page.locator("text=Stage 5 Citizen Confirmation")).toBeVisible();

    // 4. Update the Full Name field
    const modalInput = page.locator(".fixed input").first();
    await modalInput.fill("VIKRAM S MEHRA");

    // 5. Save changes
    const saveBtn = page.locator("button:has-text('Save Edits')").or(page.locator("button:has-text('Confirm & Verify')")).or(page.locator("button:has-text('Save & Confirm Fields')"));
    await expect(saveBtn.first()).toBeVisible();
    await saveBtn.first().click();

    // 6. Verify success notification or modal closes
    await expect(page.locator("h3:has-text('Review Extracted Demographic Fields')")).not.toBeVisible({ timeout: 10000 });
  });
});

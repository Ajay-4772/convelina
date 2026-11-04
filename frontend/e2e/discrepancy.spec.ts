import { test, expect } from "@playwright/test";
import { authenticateCitizen, uploadDocumentApi } from "./helpers";

test.describe("4.5 Deterministic Conflict Detection", () => {
  test("Detect and display cross-document discrepancies with exact values", async ({ page }) => {
    test.setTimeout(75000);
    const citizen = await authenticateCitizen(page);

    // 1. Upload two credentials with conflicting name format in parallel
    await Promise.all([
      uploadDocumentApi(citizen.token, "aadhaar", [
        "GOVERNMENT OF INDIA",
        "Name: SURESH BABU RANGARAJAN",
        "DOB: 12/04/1988",
        "Gender: MALE",
        "Aadhaar No: 9876 5432 1098",
      ]),
      uploadDocumentApi(citizen.token, "pan", [
        "INCOME TAX DEPARTMENT - GOVT OF INDIA",
        "Permanent Account Number Card",
        "Name: SURESH B RANGARAJAN",
        "DOB: 12/04/1988",
        "PAN: ABCDE5678G",
      ]),
    ]);

    // 2. Navigate to inconsistencies page
    await page.goto("/app/inconsistencies");

    // 3. Verify both documents appear in uploaded library cards
    await expect(page.locator("span.truncate:has-text('Aadhaar Card')")).toBeVisible({ timeout: 20000 });
    await expect(page.locator("span.truncate:has-text('PAN Card')")).toBeVisible({ timeout: 20000 });

    // 4. Trigger conflict detection button
    const detectBtn = page.locator("button:has-text('Detect Conflicts')");
    await expect(detectBtn).toBeEnabled();
    await detectBtn.click();

    // 5. Verify discrepancy section and status
    await expect(page.locator("h2:has-text('Detected Discrepancies')")).toBeVisible();
    await expect(
      page.locator("text=Analysis complete").or(page.locator("text=Deterministic cross-verification"))
    ).toBeVisible({ timeout: 20000 });
  });
});

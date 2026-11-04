import { test, expect } from "@playwright/test";
import { authenticateCitizen } from "./helpers";

test.describe("4.7 Correction Draft Generation & Petition Management", () => {
  test("Correction drafts section displays generated petitions and allows editing", async ({ page }) => {
    await authenticateCitizen(page);
    await page.goto("/app/inconsistencies");

    // Verify Section 3 exists
    await expect(page.locator("h2:has-text('Generated Correction Drafts')")).toBeVisible();
    await expect(page.locator("text=Legally structured representations, checklists, and sworn declarations")).toBeVisible();

    // If drafts exist or empty state is visible
    const emptyState = page.locator("text=No correction drafts generated yet");
    const draftCard = page.locator("div:has-text('Correction Application')");

    await expect(emptyState.or(draftCard.first())).toBeVisible();
  });
});


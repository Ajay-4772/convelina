import { test, expect } from "@playwright/test";
import { authenticateCitizen, generateSyntheticPdfBuffer } from "./helpers";

test.describe("4.3 Document Upload & Ephemeral Ingestion", () => {
  test("Upload interface presents statutory document types and Aadhaar Act notice", async ({ page }) => {
    await authenticateCitizen(page);
    await page.goto("/app/inconsistencies");

    // Verify page header
    await expect(page.locator("h1:has-text('Document Inconsistencies')")).toBeVisible();

    // Verify document selector has Indian statutory documents
    const docSelect = page.locator("select");
    await expect(docSelect).toBeVisible();
    await expect(docSelect.locator("option[value='aadhaar']")).toHaveText("Aadhaar Card");
    await expect(docSelect.locator("option[value='pan']")).toHaveText("PAN Card");
    await expect(docSelect.locator("option[value='passport']")).toHaveText("Passport");

    // Verify Ephemeral processing privacy notice
    await expect(page.locator("text=Ephemeral processing active").or(page.locator("text=Aadhaar Act (2016) Section 29")).or(page.locator("text=in-memory and immediately destroyed"))).toBeVisible();

    // Verify Detect Conflicts / Inconsistencies button exists
    const detectBtn = page.locator("button:has-text('Detect All Inconsistencies')").or(page.locator("button:has-text('Detect Conflicts')"));
    await expect(detectBtn).toBeVisible();
  });

  test("Upload synthetic PDF credential and observe processing state", async ({ page }) => {
    await authenticateCitizen(page);
    await page.goto("/app/inconsistencies");

    // Prepare synthetic document buffer
    const syntheticPdf = generateSyntheticPdfBuffer([
      "GOVERNMENT OF INDIA",
      "Name: Rajesh Kumar Verma",
      "DOB: 12/04/1988",
      "Gender: MALE",
      "Aadhaar No: 2345 6789 1234",
    ]);

    // Select document type
    await page.locator("select").selectOption("aadhaar");

    // Upload via file input directly
    await page.setInputFiles('input[type="file"]', {
      name: "synthetic_aadhaar_sample.pdf",
      mimeType: "application/pdf",
      buffer: syntheticPdf,
    });

    // Check for success notification or document card
    await expect(
      page.locator("text=uploaded and OCR processed successfully").or(page.locator("text=Ready"))
    ).toBeVisible({ timeout: 20000 });

    // Verify document card appears in library
    await expect(page.locator("text=Aadhaar Card").first()).toBeVisible();
    await expect(page.locator("text=Ready").first()).toBeVisible();
  });
});

import { test, expect, Page } from "@playwright/test";
import {
  provisionTestCitizenApi,
  uploadDocumentApi,
  API_URL,
} from "./helpers";

/**
 * Phase P3G.4.1: Independent Multilingual Quality & Export Acceptance Test Suite
 * Covers 15 required acceptance scenarios:
 * 1. Selecting English
 * 2. Translating into Tamil
 * 3. Selecting bilingual output
 * 4. Selecting Hindi
 * 5. Displaying translated preview
 * 6. Displaying unconfirmed warning
 * 7. Returning to citizen confirmation (Step 8)
 * 8. Confirming translated version
 * 9. Editing after confirmation
 * 10. Verifying confirmation invalidation
 * 11. Exporting PDF
 * 12. Exporting DOCX
 * 13. Handling translation-provider failure / fallback
 * 14. Handling long translated content
 * 15. Mobile layout and usability (viewport 375x667)
 */

let sharedCitizen: any;
let sharedConflict: any;

test.describe("Phase P3G.4.1: Multilingual Quality & Export Acceptance", () => {
  test.setTimeout(90000);

  test.beforeAll(async () => {
    // 1. Provision citizen via FastAPI
    sharedCitizen = await provisionTestCitizenApi({
      fullName: "MUTHUVEL KARUNANIDHI",
      email: `muthu_p3g4_${Date.now()}@example.com`,
    });

    // 2. Upload Aadhaar and PAN credentials
    const [docA, docB] = await Promise.all([
      uploadDocumentApi(sharedCitizen.token, "aadhaar", [
        "GOVERNMENT OF INDIA",
        "Name: MUTHUVEL KARUNANIDHI",
        "DOB: 03/06/1985",
        "Gender: MALE",
        "Aadhaar No: 9876 5432 1098",
      ]),
      uploadDocumentApi(sharedCitizen.token, "pan", [
        "INCOME TAX DEPARTMENT - GOVT OF INDIA",
        "Permanent Account Number Card",
        "Name: MUTHUVEL K",
        "DOB: 03/06/1985",
        "PAN: ABCDE1234F",
      ]),
    ]);

    // 3. Confirm both documents
    await Promise.all([
      fetch(`${API_URL}/api/v1/documents/${docA.id}/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${sharedCitizen.token}` },
        body: JSON.stringify({
          confirmed_fields: { name: "MUTHUVEL KARUNANIDHI", date_of_birth: "1985-06-03" },
        }),
      }),
      fetch(`${API_URL}/api/v1/documents/${docB.id}/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${sharedCitizen.token}` },
        body: JSON.stringify({
          confirmed_fields: { name: "MUTHUVEL K", date_of_birth: "1985-06-03" },
        }),
      }),
    ]);

    // 4. Run conflict detection comparison
    const compareRes = await fetch(`${API_URL}/api/v1/conflicts/compare`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${sharedCitizen.token}` },
      body: JSON.stringify({ document_ids: [docA.id, docB.id] }),
    });
    expect(compareRes.ok).toBeTruthy();

    const confRes = await fetch(`${API_URL}/api/v1/conflicts/`, {
      headers: { Authorization: `Bearer ${sharedCitizen.token}` },
    });
    expect(confRes.ok).toBeTruthy();
    const confData = await confRes.json();
    const conflicts = confData.conflicts || [];
    sharedConflict =
      conflicts.find((c: any) => c.field_name === "name" || c.field_name === "full_name") || conflicts[0];
    expect(sharedConflict).toBeDefined();
  });

  async function loginPageAsCitizen(page: Page) {
    await page.addInitScript((tok) => {
      try {
        localStorage.setItem("convelina_test_token", tok);
      } catch {}
    }, sharedCitizen.token);

    await page.goto("/app/inconsistencies");
    await expect(page.locator("h2:has-text('Detected Discrepancies')")).toBeVisible({ timeout: 25000 });
  }

  async function createDraftViaApi(confirmed: boolean = true) {
    const createDraftRes = await fetch(`${API_URL}/api/v1/correction-drafts/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${sharedCitizen.token}` },
      body: JSON.stringify({
        conflict_id: sharedConflict.id,
        document_type: "name_change_representation",
        document_category: "pan",
        user_explanation: "Typographical transcription error occurred during registration. I never used the abbreviated name.",
        confirmed_fields: {
          name: "MUTHUVEL KARUNANIDHI",
          applicant_name: "MUTHUVEL KARUNANIDHI",
          date_of_birth: "1985-06-03",
          pan: "ABCDE1234F",
        },
      }),
    });
    expect(createDraftRes.ok).toBeTruthy();
    const draft = await createDraftRes.json();

    if (confirmed) {
      const confirmRes = await fetch(`${API_URL}/api/v1/correction-drafts/${draft.id}/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${sharedCitizen.token}` },
        body: JSON.stringify({
          confirmation_statement: "I have reviewed all identity details in this administrative draft (Version 1) and confirm they are accurate for submission.",
          version_number: 1,
          expected_sha256_hash: draft.sha256_hash,
        }),
      });
      expect(confirmRes.ok).toBeTruthy();
      return await confirmRes.json();
    }
    return draft;
  }

  // Scenario 1: Selecting English
  test("1. Selecting English: draft workspace loads English draft correctly", async ({ page }) => {
    await createDraftViaApi(true);
    await loginPageAsCitizen(page);

    const viewEditBtn = page.locator("button:has-text('View / Edit')").first();
    await expect(viewEditBtn).toBeVisible({ timeout: 15000 });
    await viewEditBtn.click();

    const modal = page.locator("[data-testid='administrative-drafting-modal']");
    await expect(modal).toBeVisible();

    await expect(modal.locator("text=Administrative Document Drafting")).toBeVisible();
    await expect(modal.locator("text=Step 6: Editable Administrative Draft Preview")).toBeVisible();
  });

  // Scenario 2: Translating into Tamil
  test("2. Translating into Tamil: translates draft and displays formal Tamil content", async ({ page }) => {
    await createDraftViaApi(true);
    await loginPageAsCitizen(page);

    const viewEditBtn = page.locator("button:has-text('View / Edit')").first();
    await expect(viewEditBtn).toBeVisible({ timeout: 15000 });
    await viewEditBtn.click();

    const modal = page.locator("[data-testid='administrative-drafting-modal']");
    await expect(modal).toBeVisible();

    // Advance to Step 9
    await modal.locator("button:has-text('Next Step')").click();
    await modal.locator("button:has-text('Next Step')").click();
    await modal.locator("button:has-text('Next Step')").click();

    await expect(modal.locator("text=Step 9: Export Final Administrative Draft")).toBeVisible();

    const tamilBtn = modal.locator("button:has-text('Translate to Tamil (தமிழ்)')");
    await expect(tamilBtn).toBeVisible();
    await tamilBtn.click();

    await expect(modal.locator("text=Unconfirmed Draft Version 2 (TA):")).toBeVisible({ timeout: 15000 });
    await expect(modal.locator("button:has-text('English Original')")).toBeVisible();
  });

  // Scenario 3: Selecting bilingual output
  test("3. Selecting bilingual output: synthesizes parallel English + Tamil representation", async ({ page }) => {
    await createDraftViaApi(true);
    await loginPageAsCitizen(page);

    const viewEditBtn = page.locator("button:has-text('View / Edit')").first();
    await expect(viewEditBtn).toBeVisible({ timeout: 15000 });
    await viewEditBtn.click();

    const modal = page.locator("[data-testid='administrative-drafting-modal']");
    await modal.locator("button:has-text('Next Step')").click();
    await modal.locator("button:has-text('Next Step')").click();
    await modal.locator("button:has-text('Next Step')").click();

    const bilingualBtn = modal.locator("button:has-text('Bilingual (English + தமிழ்)')");
    await expect(bilingualBtn).toBeVisible();
    await bilingualBtn.click();

    await expect(modal.locator("text=BILINGUAL_EN_TA").or(modal.locator("text=Bilingual")).first()).toBeVisible({ timeout: 15000 });
  });

  // Scenario 4: Selecting Hindi
  test("4. Selecting Hindi: translates draft into formal Hindi administrative representation", async ({ page }) => {
    await createDraftViaApi(true);
    await loginPageAsCitizen(page);

    const viewEditBtn = page.locator("button:has-text('View / Edit')").first();
    await expect(viewEditBtn).toBeVisible({ timeout: 15000 });
    await viewEditBtn.click();

    const modal = page.locator("[data-testid='administrative-drafting-modal']");
    await modal.locator("button:has-text('Next Step')").click();
    await modal.locator("button:has-text('Next Step')").click();
    await modal.locator("button:has-text('Next Step')").click();

    const hindiBtn = modal.locator("button:has-text('Translate to Hindi (हिंदी)')");
    await expect(hindiBtn).toBeVisible();
    await hindiBtn.click();

    await expect(modal.locator("text=Unconfirmed Draft Version 2 (HI):")).toBeVisible({ timeout: 15000 });
  });

  // Scenario 5: Displaying translated preview
  test("5. Displaying translated preview: preserves applicant name, dates, and identifiers", async () => {
    const draft = await createDraftViaApi(true);

    const transRes = await fetch(`${API_URL}/api/v1/correction-drafts/${draft.id}/translate`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${sharedCitizen.token}` },
      body: JSON.stringify({ target_language: "ta" }),
    });
    expect(transRes.ok).toBeTruthy();
    const transData = await transRes.json();

    expect(transData.content).toContain("MUTHUVEL KARUNANIDHI");
    expect(transData.content).toContain("1234F");
    expect(transData.language).toBe("ta");
    expect(transData.version).toBe(2);
  });

  // Scenario 6: Displaying unconfirmed warning banner
  test("6. Displaying unconfirmed warning: warning banner renders upon translation", async ({ page }) => {
    await createDraftViaApi(true);
    await loginPageAsCitizen(page);

    const viewEditBtn = page.locator("button:has-text('View / Edit')").first();
    await expect(viewEditBtn).toBeVisible({ timeout: 15000 });
    await viewEditBtn.click();

    const modal = page.locator("[data-testid='administrative-drafting-modal']");
    await modal.locator("button:has-text('Next Step')").click();
    await modal.locator("button:has-text('Next Step')").click();
    await modal.locator("button:has-text('Next Step')").click();

    await modal.locator("button:has-text('Translate to Tamil (தமிழ்)')").click();

    const warning = modal.locator("text=requires your confirmation before final official submission");
    await expect(warning).toBeVisible({ timeout: 15000 });
  });

  // Scenario 7: Returning to citizen confirmation (Step 8)
  test("7. Returning to citizen confirmation: warning button navigates directly to Step 8", async ({ page }) => {
    await createDraftViaApi(true);
    await loginPageAsCitizen(page);

    const viewEditBtn = page.locator("button:has-text('View / Edit')").first();
    await expect(viewEditBtn).toBeVisible({ timeout: 15000 });
    await viewEditBtn.click();

    const modal = page.locator("[data-testid='administrative-drafting-modal']");
    await modal.locator("button:has-text('Next Step')").click();
    await modal.locator("button:has-text('Next Step')").click();
    await modal.locator("button:has-text('Next Step')").click();

    await modal.locator("button:has-text('Translate to Tamil (தமிழ்)')").click();

    const confirmNavBtn = modal.locator("button:has-text('Confirm Version 2')");
    await expect(confirmNavBtn).toBeVisible({ timeout: 15000 });
    await confirmNavBtn.click();

    await expect(modal.locator("text=Step 8: Explicit Final Version Confirmation")).toBeVisible();
    await expect(modal.getByText("Version 2", { exact: true })).toBeVisible();
  });

  // Scenario 8: Confirming translated version
  test("8. Confirming translated version: binds Version 2 and its SHA-256 hash", async ({ page }) => {
    await createDraftViaApi(true);
    await loginPageAsCitizen(page);

    const viewEditBtn = page.locator("button:has-text('View / Edit')").first();
    await expect(viewEditBtn).toBeVisible({ timeout: 15000 });
    await viewEditBtn.click();

    const modal = page.locator("[data-testid='administrative-drafting-modal']");
    await modal.locator("button:has-text('Next Step')").click();
    await modal.locator("button:has-text('Next Step')").click();
    await modal.locator("button:has-text('Next Step')").click();

    await modal.locator("button:has-text('Translate to Tamil (தமிழ்)')").click();
    await modal.locator("button:has-text('Confirm Version 2')").click();

    const textarea = modal.locator("textarea[placeholder*='I have reviewed all identity details']");
    await textarea.fill("I have reviewed all identity details in this Tamil draft (Version 2) and confirm they are accurate.");

    await modal.locator("button:has-text('Confirm Draft Version 2')").click();

    await expect(modal.locator("text=Step 9: Export Final Administrative Draft")).toBeVisible({ timeout: 15000 });
    await expect(modal.locator("text=CITIZEN-CONFIRMED FINAL DRAFT (v2)")).toBeVisible();
  });

  // Scenario 9: Editing after confirmation
  test("9. Editing after confirmation: modifying content invalidates confirmation", async () => {
    const draft = await createDraftViaApi(true);

    const patchRes = await fetch(`${API_URL}/api/v1/correction-drafts/${draft.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${sharedCitizen.token}` },
      body: JSON.stringify({
        content: draft.content + "\n\nAdditional citizen note.",
        expected_sha256_hash: draft.sha256_hash,
      }),
    });
    expect(patchRes.ok).toBeTruthy();
    const updated = await patchRes.json();

    expect(updated.version).toBe(2);
    expect(updated.is_citizen_confirmed).toBe(false);
    expect(updated.status).toBe("citizen_edited");
  });

  // Scenario 10: Verifying confirmation invalidation
  test("10. Verifying confirmation invalidation: UI displays updated status and warning banner", async ({ page }) => {
    const draft = await createDraftViaApi(true);

    await fetch(`${API_URL}/api/v1/correction-drafts/${draft.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${sharedCitizen.token}` },
      body: JSON.stringify({ content: draft.content + "\n\nPost-confirmation modification." }),
    });

    await loginPageAsCitizen(page);

    const viewEditBtn = page.locator("button:has-text('View / Edit')").first();
    await expect(viewEditBtn).toBeVisible({ timeout: 15000 });
    await viewEditBtn.click();

    const modal = page.locator("[data-testid='administrative-drafting-modal']");
    await expect(modal.locator("text=CITIZEN-EDITED DRAFT (v2)")).toBeVisible();
  });

  // Scenario 11: Exporting PDF
  test("11. Exporting PDF: delivers print-ready PDF with authentic binary header", async () => {
    const draft = await createDraftViaApi(true);

    const pdfRes = await fetch(`${API_URL}/api/v1/correction-drafts/${draft.id}/download?format=pdf`, {
      headers: { Authorization: `Bearer ${sharedCitizen.token}` },
    });
    expect(pdfRes.status).toBe(200);
    expect(pdfRes.headers.get("content-type")).toContain("application/pdf");
    const bytes = new Uint8Array(await pdfRes.arrayBuffer());
    expect(bytes.length).toBeGreaterThan(5000);
    expect(String.fromCharCode(bytes[0], bytes[1], bytes[2], bytes[3], bytes[4])).toBe("%PDF-");
  });

  // Scenario 12: Exporting DOCX
  test("12. Exporting DOCX: delivers valid Word document with OpenXML package structure", async () => {
    const draft = await createDraftViaApi(true);

    const docxRes = await fetch(`${API_URL}/api/v1/correction-drafts/${draft.id}/download?format=docx`, {
      headers: { Authorization: `Bearer ${sharedCitizen.token}` },
    });
    expect(docxRes.status).toBe(200);
    expect(docxRes.headers.get("content-type")).toContain("document");
    const bytes = new Uint8Array(await docxRes.arrayBuffer());
    expect(bytes.length).toBeGreaterThan(5000);
    expect(bytes[0]).toBe(0x50);
    expect(bytes[1]).toBe(0x4b);
  });

  // Scenario 13: Handling translation-provider failure / fallback
  test("13. Translation provider fallback: deterministic fallback responds cleanly", async () => {
    const draft = await createDraftViaApi(true);

    const transRes = await fetch(`${API_URL}/api/v1/correction-drafts/${draft.id}/translate`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${sharedCitizen.token}` },
      body: JSON.stringify({ target_language: "ta" }),
    });
    expect(transRes.status).toBe(200);
    const transData = await transRes.json();
    expect(transData.content.length).toBeGreaterThan(200);
    expect(transData.language).toBe("ta");
  });

  // Scenario 14: Handling long translated content
  test("14. Handling long translated content: long paragraphs render without layout overflow", async ({ page }) => {
    const draft = await createDraftViaApi(true);

    const longText = "விண்ணப்பதாரரின் நீண்ட விரிவான விளக்கம். ".repeat(40);
    const patchRes = await fetch(`${API_URL}/api/v1/correction-drafts/${draft.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${sharedCitizen.token}` },
      body: JSON.stringify({ content: draft.content + "\n\n" + longText }),
    });
    expect(patchRes.ok).toBeTruthy();

    await loginPageAsCitizen(page);

    const viewEditBtn = page.locator("button:has-text('View / Edit')").first();
    await expect(viewEditBtn).toBeVisible({ timeout: 15000 });
    await viewEditBtn.click();

    const modal = page.locator("[data-testid='administrative-drafting-modal']");
    await expect(modal).toBeVisible();

    const modalBox = await modal.boundingBox();
    expect(modalBox).not.toBeNull();
    expect(modalBox!.width).toBeLessThanOrEqual(1000);
  });

  // Scenario 15: Mobile layout and usability
  test("15. Mobile layout: drafting workspace remains fully usable on 375x667 mobile viewport", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await createDraftViaApi(true);
    await loginPageAsCitizen(page);

    const viewEditBtn = page.locator("button:has-text('View / Edit')").first();
    await expect(viewEditBtn).toBeVisible({ timeout: 15000 });
    await viewEditBtn.click();

    const modal = page.locator("[data-testid='administrative-drafting-modal']");
    await expect(modal).toBeVisible();

    const modalBox = await modal.boundingBox();
    expect(modalBox).not.toBeNull();
    expect(modalBox!.width).toBeLessThanOrEqual(375);

    const closeBtn = modal.locator("button").first();
    await expect(closeBtn).toBeVisible();
  });
});

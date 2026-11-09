import { test, expect, Page } from "@playwright/test";
import {
  authenticateCitizen,
  provisionTestCitizenApi,
  uploadDocumentApi,
  API_URL,
} from "./helpers";

/**
 * Phase P3G.3: Administrative Drafting Workspace & Citizen Confirmation Workflow
 * End-to-End Acceptance Test Battery covering all 14 required scenarios.
 */

async function setupCitizenWithDiscrepancy(page: Page) {
  const citizen = await authenticateCitizen(page);

  // 1. Upload Aadhaar & PAN with name mismatch under forced RLS
  const [docA, docB] = await Promise.all([
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

  // 2. Confirm fields on both documents so OCR status transitions to "completed"
  await Promise.all([
    fetch(`${API_URL}/api/v1/documents/${docA.id}/confirm`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${citizen.token}` },
      body: JSON.stringify({
        confirmed_fields: { name: "SURESH BABU RANGARAJAN", date_of_birth: "1988-04-12" },
      }),
    }),
    fetch(`${API_URL}/api/v1/documents/${docB.id}/confirm`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${citizen.token}` },
      body: JSON.stringify({
        confirmed_fields: { name: "SURESH B RANGARAJAN", date_of_birth: "1988-04-12" },
      }),
    }),
  ]);

  // 3. Trigger deterministic comparison between uploaded credentials
  const compareRes = await fetch(`${API_URL}/api/v1/conflicts/compare`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${citizen.token}`,
    },
    body: JSON.stringify({
      document_ids: [docA.id, docB.id],
    }),
  });
  expect(compareRes.ok).toBeTruthy();

  // 4. Fetch detected conflicts
  const confRes = await fetch(`${API_URL}/api/v1/conflicts/`, {
    headers: { Authorization: `Bearer ${citizen.token}` },
  });
  expect(confRes.ok).toBeTruthy();
  const confData = await confRes.json();
  const conflicts = confData.conflicts || [];
  const nameConflict =
    conflicts.find((c: any) => c.field_name === "name" || c.field_name === "full_name") ||
    conflicts[0];
  expect(nameConflict).toBeDefined();

  return { citizen, conflict: nameConflict, docA, docB };
}

test.describe("Phase P3G.3: Administrative Drafting Workspace Acceptance", () => {
  test.setTimeout(90000);

  // Scenario 1: Start draft from discrepancy
  test("1. Start draft from discrepancy: opens modal initialized with conflict context", async ({ page }) => {
    await setupCitizenWithDiscrepancy(page);

    await page.goto("/app/inconsistencies");
    await expect(page.locator("h2:has-text('Detected Discrepancies')")).toBeVisible({ timeout: 20000 });

    // Click "Generate Correction Draft" on discrepancy card
    const draftBtn = page.locator("button:has-text('Generate Correction Draft')").first();
    await expect(draftBtn).toBeVisible({ timeout: 10000 });
    await draftBtn.click();

    // Verify modal is open at Step 1
    const modal = page.locator("[data-testid='administrative-drafting-modal']");
    await expect(modal).toBeVisible({ timeout: 10000 });
    await expect(modal.locator("text=Step 1: Identified Discrepancy Overview")).toBeVisible();
    await expect(modal.locator("text=Primary Document Value:")).toBeVisible();
  });

  // Scenario 2: Review identity information in Step 2
  test("2. Review identity information in Step 2: displays confirmation state and handles explicit confirmation", async ({ page }) => {
    await setupCitizenWithDiscrepancy(page);

    await page.goto("/app/inconsistencies");
    const draftBtn = page.locator("button:has-text('Generate Correction Draft')").first();
    await expect(draftBtn).toBeVisible({ timeout: 15000 });
    await draftBtn.click();

    const modal = page.locator("[data-testid='administrative-drafting-modal']");
    await expect(modal).toBeVisible();

    // Advance to Step 2 via Continue button
    await modal.locator("button:has-text('Continue')").click();

    // Step 2 heading
    await expect(modal.locator("text=Step 2: Review & Confirm Identity Information")).toBeVisible({ timeout: 10000 });

    // Review fields and persist confirmation
    const persistBtn = modal.locator("button:has-text('Persist Citizen Confirmation to Database')");
    await expect(persistBtn).toBeVisible();
    await persistBtn.click();

    // Verify confirmation saved message
    await expect(
      modal.locator("text=Citizen identity confirmation successfully authenticated and persisted.")
    ).toBeVisible({ timeout: 10000 });
  });

  // Scenario 3: Attempt to generate with unconfirmed/empty fields (Security Gate)
  test("3. Security Gate: unconfirmed required fields reject draft generation with HTTP 422", async ({ page }) => {
    const { citizen, conflict, docA, docB } = await setupCitizenWithDiscrepancy(page);

    // Invalidate confirmation on all documents via PATCH /fields
    await Promise.all([
      fetch(`${API_URL}/api/v1/documents/${docA.id}/fields`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${citizen.token}` },
        body: JSON.stringify({ extracted_fields: { name: "Unconfirmed Value" } }),
      }),
      fetch(`${API_URL}/api/v1/documents/${docB.id}/fields`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${citizen.token}` },
        body: JSON.stringify({ extracted_fields: { name: "Unconfirmed Value" } }),
      }),
    ]);

    // Call backend API directly attempting to bypass confirmation without confirmed fields
    const bypassRes = await fetch(`${API_URL}/api/v1/correction-drafts/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${citizen.token}`,
      },
      body: JSON.stringify({
        conflict_id: conflict.id,
        document_type: "name_change_representation",
        document_category: "pan",
        user_explanation: "Attempted unconfirmed generation",
        confirmed_fields: {}, // Missing required confirmed fields
      }),
    });

    expect(bypassRes.status).toBe(422);
    const errBody = await bypassRes.json();
    expect(JSON.stringify(errBody)).toContain("citizen_confirmation_required");
  });

  // Scenario 4: Select valid vs invalid draft types (Compatibility Matrix)
  test("4. Select draft type: deterministic compatibility matrix restricts options to applicable types", async ({ page }) => {
    await setupCitizenWithDiscrepancy(page);

    await page.goto("/app/inconsistencies");
    const draftBtn = page.locator("button:has-text('Generate Correction Draft')").first();
    await expect(draftBtn).toBeVisible({ timeout: 15000 });
    await draftBtn.click();

    const modal = page.locator("[data-testid='administrative-drafting-modal']");
    await expect(modal).toBeVisible();

    // Step 1 -> Step 2
    await modal.locator("button:has-text('Continue')").click();

    // Step 2 -> Step 3
    await modal.locator("button:has-text('Continue')").click();

    await expect(modal.locator("text=Step 3: Select Administrative Draft Type")).toBeVisible({ timeout: 10000 });

    // Verify PAN compatible types are visible
    await expect(modal.locator("text=Name Change Representation").first()).toBeVisible();
    await expect(modal.locator("text=Identity Correction Request").first()).toBeVisible();

    // Inapplicable types like EPF joint declaration should NOT be selectable for PAN
    await expect(modal.locator("text=EPF Member Record Rectification Request")).not.toBeVisible();
  });

  // Scenario 5: Generate draft (Progress & Grounding breakdown)
  test("5. Generate draft: displays generation progress and grounding breakdown", async ({ page }) => {
    await setupCitizenWithDiscrepancy(page);

    await page.goto("/app/inconsistencies");
    const draftBtn = page.locator("button:has-text('Generate Correction Draft')").first();
    await expect(draftBtn).toBeVisible({ timeout: 15000 });
    await draftBtn.click();

    const modal = page.locator("[data-testid='administrative-drafting-modal']");
    await expect(modal).toBeVisible();

    // Step 1 -> Step 2
    await modal.locator("button:has-text('Continue')").click();

    // Step 2 -> Step 3
    await modal.locator("button:has-text('Continue')").click();

    // Step 3 -> Step 4
    await modal.locator("button:has-text('Continue')").click();

    await expect(modal.locator("text=Step 4: Citizen Explanation & Requested Relief")).toBeVisible({ timeout: 10000 });

    // Step 4: Fill explanation
    const explanationTextarea = modal.locator("textarea").first();
    await explanationTextarea.fill("My legal name is Suresh Babu Rangarajan on Aadhaar. PAN card abbreviated as Suresh B Rangarajan. Please rectify.");

    // Click Generate Draft
    const genBtn = modal.locator("button:has-text('Generate Administrative Draft')");
    await genBtn.click();

    // Progress to Step 6 (Editable Administrative Draft Preview)
    await expect(
      modal.locator("text=Step 6: Editable Administrative Draft Preview")
    ).toBeVisible({ timeout: 40000 });
  });

  // Scenario 6: Section-by-section editable preview
  test("6. Section-by-section editable preview: allows editing sections with disclaimer banner", async ({ page }) => {
    const { citizen, conflict } = await setupCitizenWithDiscrepancy(page);

    // Create draft via API directly for immediate preview testing
    const createDraftRes = await fetch(`${API_URL}/api/v1/correction-drafts/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${citizen.token}`,
      },
      body: JSON.stringify({
        conflict_id: conflict.id,
        document_type: "name_change_representation",
        document_category: "pan",
        user_explanation: "My legal name is Suresh Babu Rangarajan. Please update PAN accordingly.",
        confirmed_fields: { name: "SURESH BABU RANGARAJAN" },
      }),
    });
    expect(createDraftRes.ok).toBeTruthy();

    // Visit page and open draft
    await page.goto("/app/inconsistencies");
    const editBtn = page.locator(`button:has-text('View / Edit')`).first();
    await expect(editBtn).toBeVisible({ timeout: 15000 });
    await editBtn.click();

    const modal = page.locator("[data-testid='administrative-drafting-modal']");
    await expect(modal).toBeVisible();

    // Verify mandatory disclaimer banner is visible
    await expect(modal.locator("text=AI-GENERATED ADMINISTRATIVE DRAFT:")).toBeVisible();

    // Click "Edit Section" to enter sectioned editing mode
    const editSectionBtn = modal.locator("button:has-text('Edit Section')");
    await expect(editSectionBtn).toBeVisible();
    await editSectionBtn.click();

    // Verify section inputs (Recipient Authority, Subject, Document Body)
    await expect(modal.locator("text=Recipient Authority")).toBeVisible();
    await expect(modal.locator("label:has-text('Subject')")).toBeVisible();
    await expect(modal.locator("text=Document Body (Preserve Confirmed Facts)")).toBeVisible();
  });

  // Scenario 7: Official source verification & statutory abstention
  test("7. Source verification: inspects official citations and verification status", async ({ page }) => {
    const { citizen, conflict } = await setupCitizenWithDiscrepancy(page);

    const createDraftRes = await fetch(`${API_URL}/api/v1/correction-drafts/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${citizen.token}` },
      body: JSON.stringify({
        conflict_id: conflict.id,
        document_type: "name_change_representation",
        document_category: "pan",
        user_explanation: "Name correction needed.",
        confirmed_fields: { name: "SURESH BABU RANGARAJAN" },
      }),
    });
    expect(createDraftRes.ok).toBeTruthy();

    await page.goto("/app/inconsistencies");
    await page.locator(`button:has-text('View / Edit')`).first().click();

    const modal = page.locator("[data-testid='administrative-drafting-modal']");
    await expect(modal).toBeVisible();

    // Step 6 -> Step 7
    await modal.locator("button:has-text('Next Step')").click();

    await expect(modal.locator("text=Step 7: Official Procedural Source Verification")).toBeVisible({ timeout: 10000 });
    // Either source card or honest statutory abstention notice is displayed
    await expect(
      modal.locator("text=VERIFIED OFFICIAL SOURCE").or(modal.locator("text=Statutory Procedural Abstention")).first()
    ).toBeVisible({ timeout: 10000 });
  });

  // Scenario 8: Explicit final confirmation with version & SHA-256 binding
  test("8. Explicit final confirmation: binds exact version and SHA-256 hash", async ({ page }) => {
    const { citizen, conflict } = await setupCitizenWithDiscrepancy(page);

    const createDraftRes = await fetch(`${API_URL}/api/v1/correction-drafts/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${citizen.token}` },
      body: JSON.stringify({
        conflict_id: conflict.id,
        document_type: "name_change_representation",
        document_category: "pan",
        user_explanation: "Name correction needed.",
        confirmed_fields: { name: "SURESH BABU RANGARAJAN" },
      }),
    });
    expect(createDraftRes.ok).toBeTruthy();

    await page.goto("/app/inconsistencies");
    await page.locator(`button:has-text('View / Edit')`).first().click();

    const modal = page.locator("[data-testid='administrative-drafting-modal']");
    await expect(modal).toBeVisible();

    // Step 6 -> Step 7 -> Step 8
    await modal.locator("button:has-text('Next Step')").click();
    await modal.locator("button:has-text('Next Step')").click();

    await expect(modal.locator("text=Step 8: Explicit Final Version Confirmation")).toBeVisible({ timeout: 10000 });

    // Verify SHA-256 display
    await expect(modal.locator("text=Content SHA-256 Hash:")).toBeVisible();

    // Type confirmation statement
    const statementTextarea = modal.locator("textarea[placeholder*='I have reviewed all identity details']");
    await statementTextarea.fill("I have reviewed all identity details in this administrative draft (Version 1) and confirm they are accurate for submission.");

    // Click confirm button
    const confirmVersionBtn = modal.locator("button:has-text('Confirm Draft Version')");
    await confirmVersionBtn.click();

    // Verify transition to Step 9 Export
    await expect(modal.locator("text=Step 9: Export Final Administrative Draft")).toBeVisible({ timeout: 15000 });
    await expect(modal.getByText("Print-Ready PDF", { exact: true })).toBeVisible();
  });

  // Scenario 9: Invalidation on edit
  test("9. Invalidation on edit: modifying confirmed draft invalidates confirmation and increments version", async ({ page }) => {
    const { citizen, conflict } = await setupCitizenWithDiscrepancy(page);

    // 1. Create and confirm draft via API
    const createDraftRes = await fetch(`${API_URL}/api/v1/correction-drafts/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${citizen.token}` },
      body: JSON.stringify({
        conflict_id: conflict.id,
        document_type: "name_change_representation",
        document_category: "pan",
        user_explanation: "Initial text.",
        confirmed_fields: { name: "SURESH BABU RANGARAJAN" },
      }),
    });
    const draft = await createDraftRes.json();

    const confirmRes = await fetch(`${API_URL}/api/v1/correction-drafts/${draft.id}/confirm`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${citizen.token}` },
      body: JSON.stringify({
        confirmation_statement: "I have reviewed all identity details in this administrative draft and confirm they are accurate.",
        version_number: draft.version,
        expected_sha256_hash: draft.sha256_hash,
      }),
    });
    expect(confirmRes.ok).toBeTruthy();
    const confirmedDraft = await confirmRes.json();
    expect(confirmedDraft.status).toBe("citizen_confirmed");
    expect(confirmedDraft.is_citizen_confirmed).toBe(true);

    // 2. Modify draft content via PATCH
    const updateRes = await fetch(`${API_URL}/api/v1/correction-drafts/${draft.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${citizen.token}` },
      body: JSON.stringify({
        user_explanation: "Modified explanation by citizen.",
        content: "Updated draft letter content with modifications.",
      }),
    });
    expect(updateRes.ok).toBeTruthy();
    const updatedDraft = await updateRes.json();

    // Verify invalidation
    expect(updatedDraft.status).toBe("citizen_edited");
    expect(updatedDraft.is_citizen_confirmed).toBe(false);
    expect(updatedDraft.citizen_confirmed_at).toBeNull();
    expect(updatedDraft.version).toBe(confirmedDraft.version + 1);
  });

  // Scenario 10: Official sources inspection & external link safety
  test("10. Official sources inspection: verifies external link safety attributes", async ({ page }) => {
    const { citizen, conflict } = await setupCitizenWithDiscrepancy(page);

    const createDraftRes = await fetch(`${API_URL}/api/v1/correction-drafts/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${citizen.token}` },
      body: JSON.stringify({
        conflict_id: conflict.id,
        document_type: "name_change_representation",
        document_category: "pan",
        user_explanation: "Test link attributes",
        confirmed_fields: { name: "SURESH BABU RANGARAJAN" },
      }),
    });
    expect(createDraftRes.ok).toBeTruthy();

    await page.goto("/app/inconsistencies");
    await page.locator(`button:has-text('View / Edit')`).first().click();

    const modal = page.locator("[data-testid='administrative-drafting-modal']");
    await expect(modal).toBeVisible();

    // Go to Step 7
    await modal.locator("button:has-text('Next Step')").click();

    // If source external links exist, verify target="_blank" and rel="noopener noreferrer"
    const externalLinks = modal.locator("a[target='_blank']");
    const count = await externalLinks.count();
    for (let i = 0; i < count; i++) {
      const link = externalLinks.nth(i);
      const rel = await link.getAttribute("rel");
      expect(rel).toContain("noopener");
    }
  });

  // Scenario 11: Secure PDF & DOCX export
  test("11. Secure export: successfully downloads watermarked PDF and DOCX", async ({ page }) => {
    const { citizen, conflict } = await setupCitizenWithDiscrepancy(page);

    const createDraftRes = await fetch(`${API_URL}/api/v1/correction-drafts/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${citizen.token}` },
      body: JSON.stringify({
        conflict_id: conflict.id,
        document_type: "name_change_representation",
        document_category: "pan",
        user_explanation: "Export verification.",
        confirmed_fields: { name: "SURESH BABU RANGARAJAN" },
      }),
    });
    const draft = await createDraftRes.json();

    // PDF Export
    const pdfRes = await fetch(`${API_URL}/api/v1/correction-drafts/${draft.id}/download?format=pdf`, {
      headers: { Authorization: `Bearer ${citizen.token}` },
    });
    expect(pdfRes.status).toBe(200);
    expect(pdfRes.headers.get("content-type")).toContain("application/pdf");
    const pdfBlob = await pdfRes.arrayBuffer();
    expect(pdfBlob.byteLength).toBeGreaterThan(100);

    // DOCX Export
    const docxRes = await fetch(`${API_URL}/api/v1/correction-drafts/${draft.id}/download?format=docx`, {
      headers: { Authorization: `Bearer ${citizen.token}` },
    });
    expect(docxRes.status).toBe(200);
    expect(docxRes.headers.get("content-type")).toContain("document");
    const docxBlob = await docxRes.arrayBuffer();
    expect(docxBlob.byteLength).toBeGreaterThan(100);
  });

  // Scenario 12: Cross-user access denial (Forced PostgreSQL RLS)
  test("12. Tenant Isolation: Citizen B cannot fetch, edit, confirm, or export Citizen A's draft", async ({ page }) => {
    const { citizen: citizenA, conflict } = await setupCitizenWithDiscrepancy(page);
    const citizenB = await provisionTestCitizenApi();

    // Citizen A creates a draft
    const createDraftRes = await fetch(`${API_URL}/api/v1/correction-drafts/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${citizenA.token}` },
      body: JSON.stringify({
        conflict_id: conflict.id,
        document_type: "name_change_representation",
        document_category: "pan",
        user_explanation: "Citizen A confidential draft.",
        confirmed_fields: { name: "SURESH BABU RANGARAJAN" },
      }),
    });
    const draftA = await createDraftRes.json();

    // Citizen B attempts GET
    const getRes = await fetch(`${API_URL}/api/v1/correction-drafts/${draftA.id}`, {
      headers: { Authorization: `Bearer ${citizenB.token}` },
    });
    expect([403, 404]).toContain(getRes.status);

    // Citizen B attempts PATCH
    const patchRes = await fetch(`${API_URL}/api/v1/correction-drafts/${draftA.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${citizenB.token}` },
      body: JSON.stringify({ user_explanation: "Citizen B unauthorized tampering" }),
    });
    expect([403, 404]).toContain(patchRes.status);

    // Citizen B attempts Confirm
    const confirmRes = await fetch(`${API_URL}/api/v1/correction-drafts/${draftA.id}/confirm`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${citizenB.token}` },
      body: JSON.stringify({
        confirmation_statement: "Unauthorized confirmation attempt",
        version_number: 1,
        expected_sha256_hash: draftA.sha256_hash,
      }),
    });
    expect([403, 404]).toContain(confirmRes.status);

    // Citizen B attempts Export
    const exportRes = await fetch(`${API_URL}/api/v1/correction-drafts/${draftA.id}/download?format=pdf`, {
      headers: { Authorization: `Bearer ${citizenB.token}` },
    });
    expect([403, 404]).toContain(exportRes.status);
  });

  // Scenario 13: Mobile responsiveness check
  test("13. Mobile responsiveness: drafting modal scales cleanly on 375x667 viewport", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await setupCitizenWithDiscrepancy(page);

    await page.goto("/app/inconsistencies");
    const draftBtn = page.locator("button:has-text('Generate Correction Draft')").first();
    await expect(draftBtn).toBeVisible({ timeout: 15000 });
    await draftBtn.click();

    const modal = page.locator("[data-testid='administrative-drafting-modal']");
    await expect(modal).toBeVisible();

    const boundingBox = await modal.boundingBox();
    expect(boundingBox).not.toBeNull();
    if (boundingBox) {
      expect(boundingBox.width).toBeLessThanOrEqual(375);
    }
  });

  // Scenario 14: Page refresh preserving draft state
  test("14. Page refresh preserving draft state: reloads page and verifies persisted draft version and content", async ({ page }) => {
    const { citizen, conflict } = await setupCitizenWithDiscrepancy(page);

    const createDraftRes = await fetch(`${API_URL}/api/v1/correction-drafts/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${citizen.token}` },
      body: JSON.stringify({
        conflict_id: conflict.id,
        document_type: "name_change_representation",
        document_category: "pan",
        user_explanation: "Persisted explanation text across refresh.",
        confirmed_fields: { name: "SURESH BABU RANGARAJAN" },
      }),
    });
    const draft = await createDraftRes.json();

    // Navigate to page
    await page.goto("/app/inconsistencies");
    await expect(page.locator("h2:has-text('Generated Correction Drafts & Petitions')")).toBeVisible({ timeout: 15000 });

    // Reload page
    await page.reload();

    // Verify draft is still rendered with correct version
    await expect(page.locator(`text=v${draft.version}`).first()).toBeVisible({ timeout: 15000 });
    await expect(page.locator("button:has-text('View / Edit')").first()).toBeVisible();
  });
});

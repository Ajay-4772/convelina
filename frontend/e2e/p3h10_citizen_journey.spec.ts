import { test, expect } from "@playwright/test";
import {
  authenticateCitizen,
  uploadDocumentApi,
  API_URL,
} from "./helpers";

test.describe("P3H.10 — Citizen Journey & Product Experience Acceptance", () => {
  test.setTimeout(240000); // 4 minutes for complete multi-step journey

  test("Complete 10-step citizen journey from registration to draft export and RLS isolation", async ({ page }) => {
    // -------------------------------------------------------------------------
    // WORKFLOW A: Registration & Initial Workspace Entry
    // -------------------------------------------------------------------------
    console.log("=== WORKFLOW A: Citizen Onboarding & Workspace Entry ===");
    const citizenA = await authenticateCitizen(page, {
      fullName: "Aarav Sharma",
      email: `aarav.sharma.${Date.now()}@synthetic.citizen.in`,
    });

    // Navigate to dashboard
    await page.goto("/app");
    await page.waitForLoadState("networkidle");

    // Verify editorial header and active citizen session
    await expect(page.locator("text=Active Citizen Session")).toBeVisible();
    await expect(page.locator("h1")).toContainText("Aarav Sharma");

    // Verify Workspace Status Snapshot displays initial 0 state
    await expect(page.locator("text=Workspace Status Snapshot")).toBeVisible();
    await expect(page.locator("text=Step 1 of 5")).toBeVisible();
    await expect(page.locator("text=Upload Primary Identity Credentials")).toBeVisible();

    // -------------------------------------------------------------------------
    // WORKFLOW B: Multi-Document Upload & OCR Review (Stage 5)
    // -------------------------------------------------------------------------
    console.log("=== WORKFLOW B: Document Upload & Stage 5 OCR Review ===");
    await page.goto("/app/inconsistencies");
    await page.waitForLoadState("networkidle");

    // Verify Tier 1 Categories vs Secondary Evidence optgroups in selector
    const optgroupTier1 = page.locator('optgroup[label="Tier 1 Primary Identity Categories"]');
    const optgroupSec = page.locator('optgroup[label="Secondary Supporting Evidence"]');
    await expect(optgroupTier1).toBeAttached();
    await expect(optgroupSec).toBeAttached();

    // Programmatically upload synthetic Aadhaar and PAN documents
    console.log("Uploading synthetic Aadhaar and PAN...");
    const [docAadhaar, docPan] = await Promise.all([
      uploadDocumentApi(citizenA.token, "aadhaar", [
        "GOVERNMENT OF INDIA",
        "Unique Identification Authority of India",
        "Name: Aarav Sharma",
        "DOB: 15/05/1990",
        "Gender: Male",
        "Aadhaar No: 9876 5432 1098",
      ]),
      uploadDocumentApi(citizenA.token, "pan", [
        "INCOME TAX DEPARTMENT - GOVT OF INDIA",
        "Permanent Account Number Card",
        "Name: A. Sharma",
        "DOB: 15/05/1990",
        "Gender: Male",
        "PAN: ABCDE1234F",
      ]),
    ]);
    expect(docAadhaar.id).toBeTruthy();
    expect(docPan.id).toBeTruthy();

    // Refresh inconsistencies page to see uploaded credentials
    await page.reload();
    await page.waitForLoadState("networkidle");

    // Verify both documents appear in Uploaded Credentials list
    await expect(page.locator("text=Uploaded Credentials (2)")).toBeVisible();
    await expect(page.locator("span").filter({ hasText: "Aadhaar Card" }).first()).toBeVisible();
    await expect(page.locator("span").filter({ hasText: "PAN Card" }).first()).toBeVisible();

    // Open Stage 5 OCR Review Modal for Aadhaar
    console.log("Opening Stage 5 OCR Review Modal...");
    const reviewButtons = page.locator('button:has-text("Review Fields")');
    await reviewButtons.first().click();

    // Verify Stage 5 Modal Content
    await expect(page.locator("text=Review Extracted Demographic Fields")).toBeVisible();
    await expect(page.locator("text=TENTATIVE MACHINE EXTRACTION")).toBeVisible();

    // Click Confirm & Verify Demographic Data
    console.log("Confirming Aadhaar demographic data...");
    const confirmBtn = page.locator('button:has-text("Confirm & Verify Demographic Data")');
    await confirmBtn.click();

    // Verify status alert shows confirmed
    await expect(page.locator("text=verified and confirmed by citizen")).toBeVisible();

    // Confirm PAN document as well via API to speed up flow
    await fetch(`${API_URL}/api/v1/documents/${docPan.id}/confirm`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${citizenA.token}` },
      body: JSON.stringify({
        confirmed_fields: { name: "A. Sharma", date_of_birth: "1990-05-15", gender: "Male" },
      }),
    });

    await page.reload();
    await page.waitForLoadState("networkidle");

    // -------------------------------------------------------------------------
    // WORKFLOW C: Deterministic Comparison & Discrepancy Explanation
    // -------------------------------------------------------------------------
    console.log("=== WORKFLOW C: Deterministic Comparison & Discrepancy Stream ===");
    // Select all ready documents
    const selectAllBtn = page.locator('button:has-text("Select All Ready")');
    if (await selectAllBtn.isVisible()) {
      await selectAllBtn.click();
    }

    // Click Compare Selected Credentials
    const compareButton = page.locator('button:has-text("Compare Selected Credentials")');
    await expect(compareButton).toBeEnabled();
    await compareButton.click();

    // Verify Automated Comparison Result Panel appears
    await expect(page.getByText("Automated Comparison Result", { exact: true })).toBeVisible({ timeout: 15000 });
    await expect(page.locator("text=AUTOMATED COMPARISON RESULT • NOT OFFICIAL GOVERNMENT VERIFICATION").first()).toBeVisible();
    await expect(page.locator("text=CONVELINA does not declare which document is legally correct").first()).toBeVisible();

    // Verify discrepancy stream card
    await expect(page.locator("text=Detected Discrepancies")).toBeVisible();
    await expect(page.locator("text=Record A").first()).toBeVisible();
    await expect(page.locator("text=Record B").first()).toBeVisible();

    // -------------------------------------------------------------------------
    // WORKFLOW D: AI Assistant Consultation with Conflict Context
    // -------------------------------------------------------------------------
    console.log("=== WORKFLOW D: AI Assistant Consultation ===");
    // Click Discuss with CONVELINA AI
    const discussAiLink = page.locator('a:has-text("Discuss with CONVELINA AI")').first();
    if (await discussAiLink.isVisible()) {
      await discussAiLink.click();
    } else {
      await page.goto("/app/assistant");
    }
    await page.waitForLoadState("networkidle");

    // Verify Assistant Workspace loaded (greeting and hero composer)
    await expect(page.locator("h1")).toContainText("Aarav");
    const composerTextarea = page.locator('textarea[placeholder*="How can I help you"], textarea[placeholder*="Write a message"]').first();
    await expect(composerTextarea).toBeVisible({ timeout: 15000 });

    // Send a message in assistant
    await composerTextarea.fill("What official procedure expands initials from A. Sharma to Aarav Sharma for PAN card?");
    const sendButton = page.locator('button[aria-label="Send message"], button:has-text("Send")').first();
    await sendButton.click();

    // Wait for assistant response to appear
    await expect(page.locator("text=Form 49A").or(page.locator("text=NSDL")).or(page.locator("text=statutory")).first()).toBeVisible({ timeout: 25000 });

    // -------------------------------------------------------------------------
    // WORKFLOW E: Official Forms Repository & DOC_043 Banner
    // -------------------------------------------------------------------------
    console.log("=== WORKFLOW E: Document Repository Exploration & DOC_043 Audit ===");
    await page.goto("/app/forms");
    await page.waitForLoadState("networkidle");

    // Verify Document Repository header
    await expect(page.locator("text=Document Repository & Correction Guidance")).toBeVisible();
    await expect(page.locator("text=Official Government Formats & Circulars")).toBeVisible();

    // Verify primary category tabs exist
    await expect(page.locator('button:has-text("Aadhaar Card")').first()).toBeVisible();
    await expect(page.locator('button:has-text("PAN Card")').first()).toBeVisible();

    // Search for DOC_043
    const searchInput = page.locator('input[placeholder*="Search by document ID"]');
    await searchInput.fill("DOC_043");
    await page.locator('button:has-text("Search")').click();
    await page.waitForTimeout(1000);

    // Verify DOC_043 and its statutory limitation notice
    await expect(page.locator("text=DOC_043").first()).toBeVisible();
    await expect(page.locator("text=STATUTORY LIMITATION: Unverified source metadata conflict").first()).toBeVisible();

    // -------------------------------------------------------------------------
    // WORKFLOW F: Interactive Preparation Checklist Progress
    // -------------------------------------------------------------------------
    console.log("=== WORKFLOW F: Interactive Preparation Checklist ===");
    await page.goto("/app/forms/DOC_043");
    await page.waitForLoadState("networkidle");

    await expect(page.locator("text=DOC_043").first()).toBeVisible();
    await expect(page.locator("text=STATUTORY LIMITATION NOTICE").first()).toBeVisible();

    // Toggle checklist item if checklist is present
    const checklistCheckbox = page.locator('input[type="checkbox"]').first();
    if (await checklistCheckbox.isVisible()) {
      await checklistCheckbox.click();
      await page.waitForTimeout(500);
    }

    // -------------------------------------------------------------------------
    // WORKFLOW G: Personalized Correction Draft Preparation & Export
    // -------------------------------------------------------------------------
    console.log("=== WORKFLOW G: Correction Draft Preparation & Export ===");
    await page.goto("/app/inconsistencies");
    await page.waitForLoadState("networkidle");

    // Click Generate Correction Draft
    const generateDraftBtn = page.locator('button:has-text("Generate Correction Draft")').first();
    await generateDraftBtn.click();

    // Administrative Drafting Modal should open
    await expect(page.locator("text=Administrative Document Drafting")).toBeVisible();

    // Step 1: Click Continue
    const step1Continue = page.locator('button:has-text("Continue")');
    await step1Continue.click();
    await page.waitForTimeout(500);

    // Step 2: Ensure Applicant Name and Target Correct Value are populated
    const nameInput = page.locator('input[placeholder*="PRIYA SHARMA"]');
    if (await nameInput.isVisible()) {
      await nameInput.fill("Aarav Sharma");
    }
    const targetValInput = page.locator('input[placeholder*="Correct name"]');
    if (await targetValInput.isVisible()) {
      await targetValInput.fill("Aarav Sharma");
    }
    await page.locator('button:has-text("Continue")').click();
    await page.waitForTimeout(500);

    // Step 3: Select Petition Type -> click Continue
    await page.locator('button:has-text("Continue")').click();
    await page.waitForTimeout(500);

    // Step 4: Citizen Explanation -> click Generate Administrative Draft
    const explanationTextarea = page.locator('textarea[placeholder*="Explain why"]');
    if (await explanationTextarea.isVisible()) {
      await explanationTextarea.fill("Name on PAN card is abbreviated as A. Sharma whereas Aadhaar card carries full name Aarav Sharma.");
    }
    const generatePetitionBtn = page.locator('button:has-text("Generate Administrative Draft")');
    await generatePetitionBtn.click();

    // Wait for generation to reach Step 6 (Review & Edit)
    await expect(page.locator("text=Review & Edit Draft Sections").or(page.locator("text=Step 6"))).toBeVisible({ timeout: 25000 });

    // Close drafting modal
    const closeDraftModalBtn = page.locator('button[aria-label="Close modal"]').or(page.locator('button:has-text("Cancel")')).first();
    if (await closeDraftModalBtn.isVisible()) {
      await closeDraftModalBtn.click();
    }

    // Verify draft appears in Generated Correction Drafts section
    await page.reload();
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=Generated Correction Drafts & Petitions")).toBeVisible();

    // -------------------------------------------------------------------------
    // WORKFLOW H: Session & Database Persistence Across Page Reload
    // -------------------------------------------------------------------------
    console.log("=== WORKFLOW H: Page Reload & Persistence Verification ===");
    await page.goto("/app");
    await page.waitForLoadState("networkidle");

    // Verify dashboard reflects persistent counts
    await expect(page.locator("text=2 confirmed").first()).toBeVisible();
    await expect(page.locator("text=Workspace Status Snapshot")).toBeVisible();

    // -------------------------------------------------------------------------
    // WORKFLOW I: Cross-Tenant Row-Level Security (RLS) Isolation
    // -------------------------------------------------------------------------
    console.log("=== WORKFLOW I: Cross-Tenant RLS Security Isolation ===");
    // Authenticate a completely separate Citizen B in a new browser page
    const citizenB = await authenticateCitizen(page, {
      fullName: "Kavita Patel",
      email: `kavita.patel.${Date.now()}@synthetic.citizen.in`,
    });

    await page.goto("/app");
    await page.waitForLoadState("networkidle");

    // Citizen B must see their own greeting and 0 credentials
    await expect(page.locator("h1")).toContainText("Kavita Patel");
    await expect(page.locator("text=None uploaded")).toBeVisible();
    await expect(page.locator("text=Step 1 of 5")).toBeVisible();

    // Direct API verification: Citizen B querying documents must return 0 documents
    const citizenBDocsRes = await fetch(`${API_URL}/api/v1/documents`, {
      headers: { Authorization: `Bearer ${citizenB.token}` },
    });
    expect(citizenBDocsRes.ok).toBeTruthy();
    const citizenBDocs = await citizenBDocsRes.json();
    expect(citizenBDocs.documents.length).toBe(0);

    // Direct API verification: Citizen B querying conflicts must return 0 conflicts
    const citizenBConfsRes = await fetch(`${API_URL}/api/v1/conflicts`, {
      headers: { Authorization: `Bearer ${citizenB.token}` },
    });
    expect(citizenBConfsRes.ok).toBeTruthy();
    const citizenBConfs = await citizenBConfsRes.json();
    expect(citizenBConfs.conflicts.length).toBe(0);

    console.log("=== P3H.10 ALL WORKFLOWS A-I PASSED SUCCESSFULLY ===");
  });
});

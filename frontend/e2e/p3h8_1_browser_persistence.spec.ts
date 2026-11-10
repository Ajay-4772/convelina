import { test, expect } from "@playwright/test";
import {
  authenticateCitizen,
  uploadDocumentApi,
  API_URL,
} from "./helpers";

test.describe("P3H.8.1 — PostgreSQL Browser Persistence & Multi-Tenant Isolation", () => {
  test("Complete Citizen A persistence and Citizen B multi-tenant isolation", async ({ page }) => {
    // -------------------------------------------------------------------------
    // PART 1: CITIZEN A WORKFLOW & PERSISTENCE
    // -------------------------------------------------------------------------
    console.log("=== Provisioning and authenticating Citizen A ===");
    const citizenA = await authenticateCitizen(page, {
      fullName: "Aarav Sharma",
      email: `citizen.a.${Date.now()}@synthetic.test`,
    });

    // 1. Upload Aadhaar & PAN with discrepancy
    console.log("Uploading synthetic Aadhaar and PAN documents...");
    const [docA, docB] = await Promise.all([
      uploadDocumentApi(citizenA.token, "aadhaar", [
        "GOVERNMENT OF INDIA",
        "Name: Aarav Sharma",
        "DOB: 15/05/1990",
        "Aadhaar No: 9876 5432 1098",
      ]),
      uploadDocumentApi(citizenA.token, "pan", [
        "INCOME TAX DEPARTMENT - GOVT OF INDIA",
        "Name: A. Sharma",
        "DOB: 15/05/1990",
        "PAN: ABCDE1234F",
      ]),
    ]);

    // 2. Confirm fields on both documents
    console.log("Confirming extracted fields...");
    await Promise.all([
      fetch(`${API_URL}/api/v1/documents/${docA.id}/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${citizenA.token}` },
        body: JSON.stringify({
          confirmed_fields: { name: "Aarav Sharma", date_of_birth: "1990-05-15" },
        }),
      }),
      fetch(`${API_URL}/api/v1/documents/${docB.id}/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${citizenA.token}` },
        body: JSON.stringify({
          confirmed_fields: { name: "A. Sharma", date_of_birth: "1990-05-15" },
        }),
      }),
    ]);

    // 3. Trigger conflict comparison
    console.log("Triggering conflict comparison...");
    const compareRes = await fetch(`${API_URL}/api/v1/conflicts/compare`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${citizenA.token}` },
      body: JSON.stringify({ document_ids: [docA.id, docB.id] }),
    });
    expect(compareRes.ok).toBeTruthy();
    const compareData = await compareRes.json();
    const conflictId = compareData.conflicts?.[0]?.id || compareData.conflicts?.[0]?.conflict_id;
    console.log(`Conflict detected: ID=${conflictId}`);

    // 4. Create an assistant conversation
    console.log("Creating assistant conversation...");
    const convRes = await fetch(`${API_URL}/api/v1/assistant/conversations`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${citizenA.token}` },
      body: JSON.stringify({ title: "Aadhaar PAN Name Discrepancy Inquiry" }),
    });
    expect(convRes.ok).toBeTruthy();
    const convData = await convRes.json();
    const conversationId = convData.id;

    // Post a message in conversation
    await fetch(`${API_URL}/api/v1/assistant/conversations/${conversationId}/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${citizenA.token}` },
      body: JSON.stringify({
        content: "What documents do I need to expand initial in Aadhaar?",
      }),
    });

    // 5. Save checklist progress in PostgreSQL
    console.log("Saving persistent checklist progress...");
    const checkRes = await fetch(`${API_URL}/api/v1/repository/checklists/aadhaar_name_update/progress`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${citizenA.token}` },
      body: JSON.stringify({
        item_id: "REQ_AAD_NAME_INITIAL_EXPANSION_04",
        is_completed: true,
      }),
    });
    expect(checkRes.ok).toBeTruthy();
    const checkData = await checkRes.json();
    expect(checkData.completed_items).toContain("REQ_AAD_NAME_INITIAL_EXPANSION_04");

    // 6. Generate a correction draft
    console.log("Generating correction draft...");
    let draftId: string | null = null;
    if (conflictId) {
      const draftRes = await fetch(`${API_URL}/api/v1/correction-drafts`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${citizenA.token}` },
        body: JSON.stringify({
          document_type: "annexure_e",
          document_category: "aadhaar",
          conflict_id: conflictId,
          confirmed_fields: { name: "Aarav Sharma" },
        }),
      });
      if (draftRes.ok) {
        const draftData = await draftRes.json();
        draftId = draftData.id;
        console.log(`Draft created: ID=${draftId}`);
      }
    }

    // 7. Verify UI views & browser refresh persistence
    console.log("Navigating to Citizen Dashboard (/app)...");
    await page.goto("/app");
    await expect(page.locator("h1:has-text('Aarav Sharma')")).toBeVisible({ timeout: 15000 });

    // Inconsistencies Hub
    console.log("Navigating to Inconsistencies Hub (/app/inconsistencies)...");
    await page.goto("/app/inconsistencies");
    await expect(page.locator("h1:has-text('Document Inconsistencies')")).toBeVisible({ timeout: 15000 });

    // Forms Checklist detail view
    console.log("Navigating to Form Detail (/app/forms/DOC_001)...");
    await page.goto("/app/forms/DOC_001");
    await page.waitForLoadState("networkidle");

    // Refresh the browser page to test persistence across reloads
    console.log("Reloading browser page to test persistent storage...");
    await page.reload();
    await page.waitForLoadState("networkidle");

    // Verify backend confirms persistence after reload
    const progressAfterReload = await fetch(`${API_URL}/api/v1/repository/checklists/aadhaar_name_update/progress`, {
      headers: { Authorization: `Bearer ${citizenA.token}` },
    }).then((r) => r.json());
    expect(progressAfterReload.completed_items).toContain("REQ_AAD_NAME_INITIAL_EXPANSION_04");

    // Navigate away and return
    console.log("Navigating away to /app and returning to verify cross-page persistence...");
    await page.goto("/app");
    await expect(page.locator("h1:has-text('Aarav Sharma')")).toBeVisible();
    await page.goto("/app/forms/DOC_001");
    await page.waitForLoadState("networkidle");

    // -------------------------------------------------------------------------
    // PART 2: CITIZEN B MULTI-TENANT ISOLATION
    // -------------------------------------------------------------------------
    console.log("=== Provisioning and authenticating Citizen B ===");
    const citizenB = await authenticateCitizen(page, {
      fullName: "Rohan Varma",
      email: `citizen.b.${Date.now()}@synthetic.test`,
    });

    // 1. Confirm Citizen A's documents are completely inaccessible to Citizen B
    console.log("Verifying Citizen B document isolation...");
    const bDocsRes = await fetch(`${API_URL}/api/v1/documents/`, {
      headers: { Authorization: `Bearer ${citizenB.token}` },
    });
    expect(bDocsRes.ok).toBeTruthy();
    const bDocs = await bDocsRes.json();
    const bDocIds = (bDocs.documents || []).map((d: any) => d.id);
    expect(bDocIds).not.toContain(docA.id);
    expect(bDocIds).not.toContain(docB.id);

    // Direct fetch of Citizen A's document by ID must return 404 under RLS
    const directDocRes = await fetch(`${API_URL}/api/v1/documents/${docA.id}`, {
      headers: { Authorization: `Bearer ${citizenB.token}` },
    });
    expect(directDocRes.status).toBe(404);

    // 2. Confirm Citizen A's conflicts are inaccessible to Citizen B
    console.log("Verifying Citizen B conflict isolation...");
    const bConfRes = await fetch(`${API_URL}/api/v1/conflicts/`, {
      headers: { Authorization: `Bearer ${citizenB.token}` },
    });
    expect(bConfRes.ok).toBeTruthy();
    const bConfs = await bConfRes.json();
    const bConfIds = (bConfs.conflicts || []).map((c: any) => c.id);
    if (conflictId) {
      expect(bConfIds).not.toContain(conflictId);
      const directConfRes = await fetch(`${API_URL}/api/v1/conflicts/${conflictId}`, {
        headers: { Authorization: `Bearer ${citizenB.token}` },
      });
      expect(directConfRes.status).toBe(404);
    }

    // 3. Confirm Citizen A's conversations are inaccessible to Citizen B
    console.log("Verifying Citizen B conversation isolation...");
    const directConvRes = await fetch(`${API_URL}/api/v1/assistant/conversations/${conversationId}/messages`, {
      headers: { Authorization: `Bearer ${citizenB.token}` },
    });
    expect(directConvRes.status).toBe(404);

    // 4. Confirm Citizen A's checklist progress is inaccessible to Citizen B
    console.log("Verifying Citizen B checklist isolation...");
    const bCheckRes = await fetch(`${API_URL}/api/v1/repository/checklists/aadhaar_name_update/progress`, {
      headers: { Authorization: `Bearer ${citizenB.token}` },
    });
    expect(bCheckRes.ok).toBeTruthy();
    const bCheckData = await bCheckRes.json();
    expect(bCheckData.completed_items).not.toContain("REQ_AAD_NAME_INITIAL_EXPANSION_04");
    expect(bCheckData.completed_items.length).toBe(0);

    // 5. Confirm Citizen A's drafts are inaccessible to Citizen B
    if (draftId) {
      console.log("Verifying Citizen B draft isolation...");
      const directDraftRes = await fetch(`${API_URL}/api/v1/correction-drafts/${draftId}`, {
        headers: { Authorization: `Bearer ${citizenB.token}` },
      });
      expect(directDraftRes.status).toBe(404);
    }

    // Citizen B browser dashboard verification
    console.log("Navigating Citizen B to Dashboard (/app)...");
    await page.goto("/app");
    await expect(page.locator("h1:has-text('Rohan Varma')")).toBeVisible({ timeout: 15000 });

    console.log("=== All browser persistence & multi-tenant isolation tests PASSED! ===");
  });
});


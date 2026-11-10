import { test, expect } from "@playwright/test";
import {
  authenticateCitizen,
  setBrowserSessionToken,
  uploadDocumentApi,
  provisionTestCitizenApi,
  API_URL,
} from "./helpers";

test.describe("P3H.9 — Application Explorer & Guided QA End-to-End Suite", () => {
  test("1. Explorer Interface, Architecture & Live Health Inspection", async ({ page }) => {
    console.log("=== Testing Development Application Explorer UI (/dev/explorer) ===");

    await page.goto("/dev/explorer");
    await page.waitForLoadState("networkidle");

    // 1. Verify Dev Banner and Title
    await expect(page.locator("text=CONVELINA DEV QA ENVIRONMENT")).toBeVisible();
    await expect(page.locator("header span:has-text('Application Explorer')")).toBeVisible();
    await expect(page.locator("text=QA & Interactive Audit")).toBeVisible();
    await expect(page.locator("h2:has-text('CONVELINA — Architecture & Mission Overview')")).toBeVisible();

    // 2. Verify Tab Navigation Buttons
    const tabs = [
      "Overview & Health",
      "Route Explorer",
      "Feature Guide",
      "Interactive Workflows",
      "Test Accounts",
      "Persistence Inspector",
      "Admin Explorer",
    ];

    for (const tabName of tabs) {
      await expect(page.locator(`button:has-text("${tabName}")`)).toBeVisible();
    }

    // 3. Verify Live Service Health Cards on Overview
    await expect(page.locator("text=FastAPI Backend")).toBeVisible();
    await expect(page.locator("text=PostgreSQL 16 Database")).toBeVisible();
    await expect(page.locator("text=Qdrant Vector Database")).toBeVisible();
    await expect(page.locator("text=Firebase Authentication")).toBeVisible();
    await expect(page.locator("text=Gemini LLM Provider")).toBeVisible();

    // Verify distinct status labels
    await expect(page.locator("span:has-text('SIMULATED')")).toBeVisible();
    await expect(page.locator("span:has-text('BLOCKED')")).toBeVisible();

    // 4. Test Tab: Route Explorer
    await page.click("button:has-text('Route Explorer')");
    await expect(page.locator("text=Application Route Directory")).toBeVisible();
    await expect(page.getByText("/app/inconsistencies", { exact: false }).first()).toBeVisible();
    await expect(page.getByText("/app/assistant", { exact: false }).first()).toBeVisible();
    await expect(page.getByText("/app/forms", { exact: false }).first()).toBeVisible();

    // 5. Test Tab: Feature Guide
    await page.click("button:has-text('Feature Guide')");
    await expect(page.locator("text=Core Features (8)")).toBeVisible();
    await expect(page.locator("text=Deterministic Conflict Detection Engine")).toBeVisible();
    await page.click("button:has-text('Conversational AI Workspace & Procedural RAG')");
    await expect(page.locator("text=What Data It Reads:")).toBeVisible();

    // 6. Test Tab: Interactive Workflows
    await page.click("button:has-text('Interactive Workflows')");
    await expect(page.locator("text=14 Guided QA Workflows")).toBeVisible();
    await expect(page.locator("button:has-text('1. Register & Sign In')")).toBeVisible();
    await expect(page.locator("button:has-text('5. Compare Two Identity Documents')")).toBeVisible();
    await expect(page.locator("button:has-text('11. Save Checklist Progress')")).toBeVisible();

    // 7. Test Tab: Test Accounts
    await page.click("button:has-text('Test Accounts')");
    await expect(page.locator("text=Aarav Sharma")).toBeVisible();
    await expect(page.locator("text=Priya Patel")).toBeVisible();
    await expect(page.locator("text=AJAY M (Platform Admin)")).toBeVisible();

    // 8. Test Tab: Admin Explorer
    await page.click("button:has-text('Admin Explorer')");
    await expect(page.locator("text=Administrator Console Explorer")).toBeVisible();
    await expect(page.locator("text=1. Real-Time Operational Metrics")).toBeVisible();
    await expect(page.locator("text=4. Form Replacement & Rejection Gate")).toBeVisible();

    console.log("=== Explorer UI inspection PASSED! ===");
  });

  test("2. Full Citizen A Workflow, Persistence & Inspector Verification", async ({ page }) => {
    test.setTimeout(120000);
    console.log("=== Provisioning Citizen A ===");
    const citizenA = await authenticateCitizen(page, {
      fullName: "Aarav Sharma",
      email: `citizen.a.${Date.now()}@synthetic.test`,
    });

    // 1. Upload Aadhaar & PAN
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
    expect(compareData.discrepancies_count).toBeGreaterThan(0);

    const confListRes = await fetch(`${API_URL}/api/v1/conflicts`, {
      headers: { Authorization: `Bearer ${citizenA.token}` },
    });
    const confList = await confListRes.json();
    expect(confList.conflicts.length).toBeGreaterThan(0);
    const conflictId = confList.conflicts[0].id;

    // 4. Create assistant conversation
    console.log("Creating assistant conversation...");
    const convRes = await fetch(`${API_URL}/api/v1/assistant/conversations`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${citizenA.token}` },
      body: JSON.stringify({
        title: "Name Discrepancy Discussion",
        conflict_id: conflictId,
      }),
    });
    expect(convRes.ok).toBeTruthy();

    // 5. Save checklist progress in PostgreSQL
    console.log("Saving persistent checklist progress...");
    const checklistRes = await fetch(`${API_URL}/api/v1/repository/checklists/aadhaar_name_update/progress`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${citizenA.token}` },
      body: JSON.stringify({
        item_id: "REQ_AAD_NAME_INITIAL_EXPANSION_04",
        is_completed: true,
      }),
    });
    expect(checklistRes.ok).toBeTruthy();

    // 6. Generate correction draft
    console.log("Generating correction draft...");
    const draftRes = await fetch(`${API_URL}/api/v1/correction-drafts`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${citizenA.token}` },
      body: JSON.stringify({
        document_type: "identity_correction_request",
        document_category: "aadhaar",
        conflict_id: conflictId,
        confirmed_fields: { name: "Aarav Sharma" },
      }),
    });
    expect(draftRes.ok).toBeTruthy();

    // 7. Test Browser Navigation & Reload Persistence
    console.log("Navigating to /app and /app/inconsistencies...");
    await page.goto("/app");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=Active Citizen Session")).toBeVisible();

    await page.goto("/app/inconsistencies");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=Inconsistencies").first()).toBeVisible();

    await page.goto("/app/forms");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=Forms").first()).toBeVisible();

    // Page Reload Test
    console.log("Reloading page to verify persistence...");
    await page.reload();
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=Forms").first()).toBeVisible();

    // 8. Open Persistence Inspector in Dev Explorer
    console.log("Opening Persistence Inspector in /dev/explorer...");
    await page.goto("/dev/explorer");
    await page.waitForLoadState("networkidle");

    await page.click("button:has-text('Persistence Inspector')");
    await page.waitForTimeout(1000);

    // Verify Citizen A's persisted records are visible in inspector
    await expect(page.locator("text=Inspecting User:")).toBeVisible();
    await expect(page.locator("span:has-text('Uploaded Documents')")).toBeVisible();
    await expect(page.locator("span:has-text('Detected Inconsistencies')")).toBeVisible();
    await expect(page.getByText("Checklist Progress", { exact: true })).toBeVisible();
    await expect(page.locator("span:has-text('Correction Drafts')")).toBeVisible();

    console.log("=== Citizen A lifecycle and Persistence Inspector PASSED! ===");
  });

  test("3. Citizen B Multi-Tenant Isolation & Zero Leakage", async ({ page }) => {
    console.log("=== Provisioning Citizen B ===");
    const citizenB = await authenticateCitizen(page, {
      fullName: "Priya Patel",
      email: `citizen.b.${Date.now()}@synthetic.test`,
    });

    // 1. Verify empty documents list
    const docsRes = await fetch(`${API_URL}/api/v1/documents`, {
      headers: { Authorization: `Bearer ${citizenB.token}` },
    });
    const docs = await docsRes.json();
    expect(docs.documents.length).toBe(0);

    // 2. Verify empty conflicts list
    const confRes = await fetch(`${API_URL}/api/v1/conflicts`, {
      headers: { Authorization: `Bearer ${citizenB.token}` },
    });
    const confs = await confRes.json();
    expect(confs.conflicts.length).toBe(0);

    // 3. Verify empty conversations list
    const convRes = await fetch(`${API_URL}/api/v1/assistant/conversations`, {
      headers: { Authorization: `Bearer ${citizenB.token}` },
    });
    const convs = await convRes.json();
    expect(convs.conversations.length).toBe(0);

    // 4. Verify empty checklist progress
    const checkRes = await fetch(`${API_URL}/api/v1/repository/checklists/aadhaar_name_update/progress`, {
      headers: { Authorization: `Bearer ${citizenB.token}` },
    });
    const checkData = await checkRes.json();
    expect(checkData.completed_items.length).toBe(0);

    // 5. Verify Citizen B Dashboard in Browser
    await page.goto("/app");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=Active Citizen Session")).toBeVisible();
    await expect(page.locator("text=Priya Patel").first()).toBeVisible();

    await page.goto("/app/inconsistencies");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=Inconsistencies").first()).toBeVisible();

    console.log("=== Citizen B multi-tenant isolation PASSED! ===");
  });

  test("4. Administrative Authorization Boundaries & Admin Console", async ({ page }) => {
    console.log("=== Testing Unauthorized Citizen Access to /admin ===");
    // Citizen session attempting to access /admin
    const citizen = await authenticateCitizen(page, {
      fullName: "Unauthorized Citizen",
      email: `unauth.${Date.now()}@synthetic.test`,
    });

    // API Level: GET /api/v1/admin/overview-stats returns 403 Forbidden
    const unauthApiRes = await fetch(`${API_URL}/api/v1/admin/overview-stats`, {
      headers: { Authorization: `Bearer ${citizen.token}` },
    });
    expect(unauthApiRes.status).toBe(403);

    // UI Level: Navigate to /admin
    await page.goto("/admin");
    await page.waitForLoadState("networkidle");

    // Expect Access Denied Screen
    await expect(page.locator("text=Access Denied")).toBeVisible();
    await expect(page.locator("text=Return to Citizen Workspace")).toBeVisible();

    // -------------------------------------------------------------------------
    // Elevate / Provision Administrator Account
    // -------------------------------------------------------------------------
    console.log("=== Provisioning Administrator Account ===");
    const adminEmail = `admin.${Date.now()}@convelina.gov.in`;

    // Provision admin via dev endpoint
    const provRes = await fetch(`${API_URL}/api/v1/dev/provision-test-account`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target: "admin" }),
    });
    expect(provRes.ok).toBeTruthy();
    const adminData = await provRes.json();

    // Admin API Level: GET /api/v1/admin/overview-stats returns 200 OK
    const adminApiRes = await fetch(`${API_URL}/api/v1/admin/overview-stats`, {
      headers: { Authorization: `Bearer ${adminData.test_token}` },
    });
    expect(adminApiRes.status).toBe(200);
    const adminStats = await adminApiRes.json();
    expect(adminStats).toHaveProperty("users");
    expect(adminStats.users).toHaveProperty("total");

    // Set admin token in browser
    await page.goto("/");
    await setBrowserSessionToken(page, adminData.test_token);

    // Navigate to /admin as Administrator
    await page.goto("/admin");
    await page.waitForLoadState("networkidle");

    // Verify Admin Console is successfully rendered
    await expect(page.locator("text=CONVELINA Admin Console")).toBeVisible();
    await expect(page.locator("text=Total Users")).toBeVisible();
    await expect(page.locator("text=Statutory Forms & Official Repository")).toBeVisible();

    console.log("=== Admin authorization boundaries & console PASSED! ===");
  });
});

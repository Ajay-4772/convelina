import { test, expect } from "@playwright/test";
import * as path from "path";

const SCREENSHOT_DIR = path.resolve(__dirname, "../../docs/screenshots");

test.describe("P3H.7 — Full Application Exploration & Acceptance Audit", () => {
  test.beforeEach(async ({ page }) => {
    // Intercept auth endpoints to support deterministic session simulation
    await page.route("**/api/v1/auth/me", async (route) => {
      const headers = route.request().headers();
      const authHeader = headers["authorization"] || "";
      
      if (authHeader.includes("admin")) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: "usr_admin_001",
            firebase_uid: "test_admin_uid",
            email: "admin@convelina.gov.in",
            full_name: "Super Administrator",
            role: "admin",
            phone_number: "+919876543200",
            created_at: "2026-01-01T00:00:00Z",
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: "usr_cit_001",
            firebase_uid: "test_citizen_uid",
            email: "citizen@example.com",
            full_name: "Aarav Sharma",
            role: "user",
            phone_number: "+919876543210",
            date_of_birth: "1992-08-15",
            address: "24, Gandhi Nagar, Bengaluru, Karnataka - 560001",
            created_at: "2026-02-15T10:30:00Z",
          }),
        });
      }
    });

    // Mock conflicts endpoint for Inconsistencies exploration
    await page.route("**/api/v1/conflicts*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          {
            id: "conf_001",
            user_id: "usr_cit_001",
            doc_a_id: "doc_aadhaar_01",
            doc_b_id: "doc_pan_01",
            doc_a_type: "aadhaar",
            doc_b_type: "pan",
            field_name: "full_name",
            value_a: "Aarav Sharma",
            value_b: "Aarav S",
            similarity_score: 0.78,
            confidence_score: 0.94,
            severity: "MAJOR",
            status: "OPEN",
            requires_manual_review: false,
            explanation: "Surname initial expansion detected between Aadhaar ('Sharma') and PAN ('S').",
            evidence: ["Aadhaar full name parsed as 'Aarav Sharma'", "PAN card name parsed as 'Aarav S'"],
            recommended_action: "Submit PAN Change Request (Form CSF) with Aadhaar as PoI.",
            created_at: "2026-03-01T12:00:00Z",
          },
          {
            id: "conf_002",
            user_id: "usr_cit_001",
            doc_a_id: "doc_aadhaar_01",
            doc_b_id: "doc_passport_01",
            doc_a_type: "aadhaar",
            doc_b_type: "passport",
            field_name: "date_of_birth",
            value_a: "1992-08-15",
            value_b: "1992-08-16",
            similarity_score: 0.85,
            confidence_score: 0.98,
            severity: "CRITICAL",
            status: "OPEN",
            requires_manual_review: true,
            explanation: "Day-of-birth disparity detected (15th vs 16th August 1992).",
            evidence: ["Aadhaar DoB: 15/08/1992", "Passport DoB: 16/08/1992"],
            recommended_action: "Provide Municipal Birth Certificate or Class 10 Certificate to resolve date discrepancy.",
            created_at: "2026-03-01T12:05:00Z",
          },
        ]),
      });
    });

    // Mock documents list endpoint
    await page.route("**/api/v1/documents", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          {
            id: "doc_aadhaar_01",
            document_type: "aadhaar",
            original_filename: "synthetic_aadhaar_card.pdf",
            ocr_status: "SUCCESS",
            is_user_confirmed: true,
            created_at: "2026-03-01T11:50:00Z",
            confirmed_fields: {
              full_name: "Aarav Sharma",
              date_of_birth: "1992-08-15",
              gender: "MALE",
              masked_id: "XXXX-XXXX-8921",
            },
          },
          {
            id: "doc_pan_01",
            document_type: "pan",
            original_filename: "synthetic_pan_card.pdf",
            ocr_status: "SUCCESS",
            is_user_confirmed: true,
            created_at: "2026-03-01T11:55:00Z",
            confirmed_fields: {
              full_name: "Aarav S",
              date_of_birth: "1992-08-15",
              masked_id: "XXXXX4921X",
            },
          },
        ]),
      });
    });

    // Mock Admin Overview Stats
    await page.route("**/api/v1/admin/overview-stats", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          users: { total: 142, admins: 2, citizens: 140 },
          documents: { total_uploaded: 428 },
          conflicts: { total_detected: 89 },
          assistant: { total_messages: 1250, forms_available: 52 },
          pki: { total_attestations: 64, active_signing_keys: 2 },
          audit: { total_events: 512 },
        }),
      });
    });

    // Mock Admin Users List
    await page.route("**/api/v1/admin/users*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          {
            id: "usr_001",
            email: "citizen@example.com",
            full_name: "Aarav Sharma",
            role: "user",
            created_at: "2026-02-15T10:30:00Z",
            document_count: 2,
            conflict_count: 2,
          },
          {
            id: "usr_admin_001",
            email: "admin@convelina.gov.in",
            full_name: "Super Administrator",
            role: "admin",
            created_at: "2026-01-01T00:00:00Z",
            document_count: 0,
            conflict_count: 0,
          },
        ]),
      });
    });

    // Mock Knowledge Corpus Status
    await page.route("**/api/v1/knowledge/corpus/status", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          corpus_version: "2026.1-p3h5",
          total_documents: 47,
          operational_core: 8,
          reference_secondary: 12,
          quarantined: 27,
          qdrant_status: "connected",
          qdrant_mode: "in_process",
          active_chunks_count: 195,
          bm25_status: "active",
        }),
      });
    });
  });

  // 1. LANDING PAGE EXPLORATION
  test("Screen 01: Landing Page (/)", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/");
    await expect(page.locator("text=CONVELINA").first()).toBeVisible({ timeout: 15000 });
    await expect(page.locator("text=Privacy Safeguards").first()).toBeVisible();
    await expect(page.locator("text=Conflict Detection").first()).toBeVisible();
    await expect(page.locator("text=Experience document clarity.").first()).toBeVisible();

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "01_landing_desktop.png"), fullPage: true });

    // Mobile Viewport
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/");
    await expect(page.locator("text=CONVELINA").first()).toBeVisible();
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "01_landing_mobile.png"), fullPage: true });
  });

  // 2. AUTHENTICATION SCREENS
  test("Screen 02 & 03: Login & Signup Screens", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });

    // Login
    await page.goto("/login");
    await expect(page.locator("h1:has-text('Welcome back')")).toBeVisible({ timeout: 15000 });
    await expect(page.locator("input[type='email']")).toBeVisible();
    await expect(page.locator("input[type='password']")).toBeVisible();
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "02_login.png") });

    // Signup
    await page.goto("/signup");
    await expect(page.locator("h1:has-text('Create account')")).toBeVisible({ timeout: 15000 });
    await expect(page.locator("input[placeholder*='Ajay Ramanathan']")).toBeVisible();
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "03_signup.png") });

    // Verify Email
    await page.goto("/verify-email");
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "04_verify_email.png") });
  });

  // 3. CITIZEN DASHBOARD & DOCUMENTS
  test("Screen 05 & 06: Citizen Setup Profile & Dashboard", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    const token = "test_token_:usr_cit_001:citizen@example.com:Aarav Sharma";
    await page.addInitScript((tok) => {
      try {
        localStorage.setItem("convelina_test_token", tok);
      } catch {}
    }, token);

    // Setup Profile Screen
    await page.goto("/setup-profile");
    await expect(page.locator("h1:has-text('Complete your profile')")).toBeVisible({ timeout: 15000 });
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "05_setup_profile.png") });

    // Dashboard
    await page.goto("/app");
    await expect(page.locator("h1:has-text('Aarav Sharma')")).toBeVisible({ timeout: 15000 });
    await expect(page.locator("text=Check Document Inconsistencies")).toBeVisible();
    await expect(page.locator("text=Ask the AI Assistant")).toBeVisible();
    await expect(page.locator("text=Browse Official Forms")).toBeVisible();
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "06_dashboard.png"), fullPage: true });
  });

  // 4. IDENTITY INCONSISTENCIES / CONFLICT HUB
  test("Screen 07: Inconsistencies & Conflict Resolution Hub", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    const token = "test_token_:usr_cit_001:citizen@example.com:Aarav Sharma";
    await page.addInitScript((tok) => {
      try {
        localStorage.setItem("convelina_test_token", tok);
      } catch {}
    }, token);

    await page.goto("/app/inconsistencies");
    await expect(page.locator("h1:has-text('Document Inconsistencies')")).toBeVisible({ timeout: 15000 });
    await expect(page.locator("text=Add Document for Reconciliation")).toBeVisible();
    await expect(page.locator("text=Upload File").first()).toBeVisible();
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "07_inconsistencies.png"), fullPage: true });
  });

  // 5. CONVERSATIONAL AI ASSISTANT
  test("Screen 08: Conversational Assistant Workspace", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    const token = "test_token_:usr_cit_001:citizen@example.com:Aarav Sharma";
    await page.addInitScript((tok) => {
      try {
        localStorage.setItem("convelina_test_token", tok);
      } catch {}
    }, token);

    await page.goto("/app/assistant");
    await expect(page.locator("textarea[placeholder*='How can I help you today?']")).toBeVisible({ timeout: 15000 });
    await expect(page.locator("text=Explain my document discrepancy").first()).toBeVisible();
    await expect(page.locator("text=Find an official correction form").first()).toBeVisible();
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "08_assistant.png"), fullPage: true });
  });

  // 6. CITIZEN DOCUMENT REPOSITORY & DETAIL VIEWS
  test("Screen 09, 10 & 11: Document Repository & Detail Views", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    const token = "test_token_:usr_cit_001:citizen@example.com:Aarav Sharma";
    await page.addInitScript((tok) => {
      try {
        localStorage.setItem("convelina_test_token", tok);
      } catch {}
    }, token);

    // Repository Catalog
    await page.goto("/app/forms");
    await expect(page.locator("h1:has-text('Document Repository & Correction Guidance')")).toBeVisible({ timeout: 15000 });
    await expect(page.locator("button:has-text('Aadhaar Card')")).toBeVisible();
    await expect(page.locator("button:has-text('PAN Card')")).toBeVisible();
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "09_repository.png"), fullPage: true });

    // Detail View: DOC_036
    await page.goto("/app/forms/DOC_036");
    await expect(page.locator("h1")).toBeVisible({ timeout: 15000 });
    await expect(page.locator("text=What is this document used for?")).toBeVisible();
    await expect(page.locator("text=Required Supporting Documents Checklist")).toBeVisible();
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "10_document_detail.png"), fullPage: true });

    // Conflict Limitation View: DOC_043
    await page.goto("/app/forms/DOC_043");
    await expect(page.locator("text=STATUTORY LIMITATION NOTICE").first()).toBeVisible({ timeout: 15000 });
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "11_doc043_limitation.png"), fullPage: true });
  });

  // 7. USER PROFILE SCREEN
  test("Screen 12: Citizen Profile & Security Management", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    const token = "test_token_:usr_cit_001:citizen@example.com:Aarav Sharma";
    await page.addInitScript((tok) => {
      try {
        localStorage.setItem("convelina_test_token", tok);
      } catch {}
    }, token);

    await page.goto("/app/profile");
    await expect(page.locator("h1:has-text('Profile & Account Settings')")).toBeVisible({ timeout: 15000 });
    await expect(page.locator("text=Aarav Sharma").first()).toBeVisible();
    await expect(page.locator("text=citizen@example.com").first()).toBeVisible();
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "12_profile.png"), fullPage: true });
  });

  // 8. ADMIN GATEWAY & PORTAL
  test("Screen 13 & 14: Admin Gateway, Authorization & Console", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });

    // A. Verify regular citizen is blocked from /admin
    const citizenToken = "test_token_:usr_cit_001:citizen@example.com:Aarav Sharma";
    await page.addInitScript((tok) => {
      try {
        localStorage.setItem("convelina_test_token", tok);
      } catch {}
    }, citizenToken);

    await page.goto("/admin");
    // Verify Access Denied card for citizen role
    await expect(page.locator("h2:has-text('Access Denied')")).toBeVisible({ timeout: 15000 });
    await expect(page.locator("text=The CONVELINA Administrator Console is restricted strictly")).toBeVisible();

    // B. Admin Login Screen
    await page.goto("/admin/login");
    await expect(page.locator("h2:has-text('CONVELINA Administration')")).toBeVisible({ timeout: 15000 });
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "13_admin_login.png") });

    // C. Authenticated Admin Console
    // Mock the backend responses for admin role and management APIs
    await page.route("**/api/v1/auth/me", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "usr_admin_001",
          firebase_uid: "usr_admin_001",
          email: "admin@convelina.gov.in",
          full_name: "Super Administrator",
          role: "admin",
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }),
      });
    });
    await page.route("**/api/v1/admin/overview-stats", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          users: { total: 42, users: 40, admins: 2 },
          documents: { total_uploaded: 156 },
          conflicts: { total_detected: 28 },
          assistant: { total_messages: 512, forms_available: 52 },
          pki: { total_attestations: 89, active_signing_keys: 1 },
          audit: { total_events: 1024 },
        }),
      });
    });
    await page.route("**/api/v1/admin/users", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          { id: "usr_admin_001", full_name: "Super Administrator", email: "admin@convelina.gov.in", role: "admin", created_at: "2026-01-01T00:00:00Z" },
          { id: "usr_cit_001", full_name: "Aarav Sharma", email: "aarav.sharma@example.com", role: "user", created_at: "2026-02-15T00:00:00Z" },
        ]),
      });
    });
    await page.route("**/api/v1/admin/system-activity", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          { id: "act_1", action: "AUTH_LOGIN", user_id: "usr_admin_001", timestamp: new Date().toISOString(), status: "SUCCESS" },
        ]),
      });
    });
    await page.route("**/api/v1/pki/keys", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          { key_id: "key_prod_ed25519_01", algorithm: "Ed25519", status: "active", created_at: "2026-01-01T00:00:00Z" },
        ]),
      });
    });
    await page.route("**/api/v1/knowledge/admin/forms", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          { form_id: "DOC_001", form_name: "Aadhaar Enrolment / Update Form", form_code: "UIDAI_ENROL_01", verification_status: "verified", version: "1.0", issuing_authority: "UIDAI" },
          { form_id: "DOC_043", form_name: "UIDAI Exceptional Update SOP", form_code: "UIDAI_SOP_043", verification_status: "needs_review", version: "1.0", issuing_authority: "UIDAI" },
        ]),
      });
    });

    const adminToken = "test_token_:usr_admin_001:admin@convelina.gov.in:Super Administrator";
    await page.evaluate((tok) => {
      localStorage.setItem("convelina_test_token", tok);
    }, adminToken);

    await page.goto("/admin");
    await expect(page.locator("text=CONVELINA Admin Console").first()).toBeVisible({ timeout: 15000 });
    await expect(page.locator("h3:has-text('User Account Directory')")).toBeVisible();
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "14_admin_dashboard.png"), fullPage: true });
  });
});

import { test, expect } from "@playwright/test";

test.describe("Phase P3H.6: Citizen Document Repository & Procedural Guidance Synthesis", () => {
  test.beforeEach(async ({ page }) => {
    // Intercept Auth endpoints to simulate authenticated citizen session
    await page.route("**/api/v1/auth/provision", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "cit_e2e_123",
          firebase_uid: "test_citizen_uid",
          email: "citizen@example.com",
          full_name: "Aarav Sharma",
          role: "user",
        }),
      });
    });

    await page.route("**/api/v1/auth/me", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "cit_e2e_123",
          firebase_uid: "test_citizen_uid",
          email: "citizen@example.com",
          full_name: "Aarav Sharma",
          role: "user",
        }),
      });
    });

    // Intercept Categories Summary endpoint
    await page.route("**/api/v1/repository/categories", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          total_resources: 52,
          categories: [
            { category: "aadhaar", label: "Aadhaar Card", count: 35 },
            { category: "pan", label: "PAN Card", count: 7 },
            { category: "passport", label: "Passport", count: 3 },
            { category: "class_10", label: "Class 10 Certificate", count: 2 },
            { category: "class_12", label: "Class 12 Certificate", count: 2 },
            { category: "epf", label: "EPF/UAN Records", count: 2 },
          ],
        }),
      });
    });

    // Intercept Personalized Guidance endpoint
    await page.route("**/api/v1/repository/guidance/personalized", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          has_conflicts: false,
          user_id: "cit_e2e_123",
          discrepancies: [],
          mandatory_disclaimer: "AUTOMATED COMPARISON RESULT — NOT OFFICIAL GOVERNMENT VERIFICATION.",
        }),
      });
    });

    // Intercept Repository Resources listing
    await page.route("**/api/v1/repository/resources*", async (route) => {
      const url = new URL(route.request().url());
      const search = url.searchParams.get("search") || "";
      const cat = url.searchParams.get("category") || "";

      let list = [
        {
          id: "res_doc_036",
          resource_id: "DOC_036",
          title: "Form 49A / PAN Change Request Form Instructions",
          issuing_authority: "Income Tax Department",
          document_category: "pan",
          document_type: "application_form",
          provenance: "OFFICIAL_ORIGINAL",
          verification_status: "VERIFIED",
          description: "Statutory instructions and requirements for PAN card reissue and name correction (Form 49A / CSF).",
          purpose: "Used by Indian citizens to request correction of name, date of birth, or reissue of PAN card with updated details.",
          source_date: "2021-04-01",
          is_official_government_form: true,
          is_synthetic_sample: false,
          human_review_required: false,
          source_conflict_flag: false,
        },
        {
          id: "res_doc_043",
          resource_id: "DOC_043",
          title: "UIDAI Regional Office Internal Exception Process (DOC_043)",
          issuing_authority: "Unique Identification Authority of India (UIDAI)",
          document_category: "aadhaar",
          document_type: "correction_procedure",
          provenance: "GOVERNMENT_REFERENCE",
          verification_status: "SOURCE_METADATA_CONFLICT",
          description: "Internal document describing administrative exception handling for Aadhaar limit violations.",
          purpose: "Internal regional office review guidelines for citizens who have exhausted standard statutory update limits.",
          source_date: "2020-03-01",
          is_official_government_form: false,
          is_synthetic_sample: false,
          human_review_required: true,
          source_conflict_flag: true,
          statutory_limitation_notice: "STATUTORY LIMITATION NOTICE: DOC_043 retains an unverified source metadata conflict.",
        },
      ];

      if (search.includes("DOC_036")) {
        list = list.filter((r) => r.resource_id === "DOC_036");
      } else if (cat === "pan") {
        list = list.filter((r) => r.document_category === "pan");
      }

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          resources: list,
          total: list.length,
          page: 1,
          page_size: 12,
          total_pages: 1,
        }),
      });
    });

    // Intercept DOC_036 Detail
    await page.route("**/api/v1/repository/resources/DOC_036", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "res_doc_036",
          resource_id: "DOC_036",
          title: "Form 49A / PAN Change Request Form Instructions",
          issuing_authority: "Income Tax Department",
          document_category: "pan",
          document_type: "application_form",
          provenance: "OFFICIAL_ORIGINAL",
          verification_status: "VERIFIED",
          description: "Statutory instructions and requirements for PAN card reissue and name correction (Form 49A / CSF).",
          purpose: "Used by Indian citizens to request correction of name, date of birth, or reissue of PAN card with updated details.",
          who_should_use: "Any citizen whose PAN card contains spelling errors, missing initials, or discrepancies compared to their Aadhaar card.",
          source_date: "2021-04-01",
          source_verification_status: "verified",
          original_file_name: "pan_correction_form_49a_instructions.pdf",
          original_file_format: "pdf",
          original_file_sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
          is_official_government_form: true,
          is_synthetic_sample: false,
          human_review_required: false,
          source_conflict_flag: false,
          related_procedures: [
            {
              procedure_id: "pan_name_correction_csf",
              title: "PAN Name & Data Correction Procedure (CSF Request)",
              target_authority: "Income Tax Department / Protean (NSDL) / UTIITSL",
              identity_category: "pan",
              is_online_available: true,
            },
          ],
          checklists: [
            {
              requirement_id: "pan_req_01",
              title: "Copy of Existing PAN Card",
              category: "pan",
              requirement_status: "VERIFIED_MANDATORY",
              supporting_source: "ITD PAN Guidelines Rule 114",
              source_verification_status: "VERIFIED",
              description: "Copy of the existing PAN card or PAN allotment letter must be attached to verify allotment.",
              mandatory: true,
            },
            {
              requirement_id: "pan_req_02",
              title: "Proof of Identity Matching Corrected Name (Aadhaar / Passport)",
              category: "pan",
              requirement_status: "VERIFIED_MANDATORY",
              supporting_source: "ITD PAN Guidelines Rule 114",
              source_verification_status: "VERIFIED",
              description: "Statutory proof of identity reflecting the requested corrected name.",
              mandatory: true,
            },
          ],
          citations: [
            {
              citation_id: "cit_itd_01",
              source_name: "ITD PAN Guidelines Rule 114",
              section_or_page: "Rule 114(4)",
              quote_or_summary: "Every applicant seeking correction of PAN particulars must furnish proof of identity, address and existing PAN.",
            },
          ],
        }),
      });
    });

    // Intercept DOC_043 Detail
    await page.route("**/api/v1/repository/resources/DOC_043", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "res_doc_043",
          resource_id: "DOC_043",
          title: "UIDAI Regional Office Internal Exception Process (DOC_043)",
          issuing_authority: "Unique Identification Authority of India (UIDAI)",
          document_category: "aadhaar",
          document_type: "correction_procedure",
          provenance: "GOVERNMENT_REFERENCE",
          verification_status: "SOURCE_METADATA_CONFLICT",
          description: "Internal document describing administrative exception handling for Aadhaar limit violations.",
          purpose: "Internal regional office review guidelines for citizens who have exhausted standard statutory update limits.",
          who_should_use: "Citizens referred to UIDAI Regional Office after multiple failed or exhausted update attempts.",
          source_date: "2020-03-01",
          source_verification_status: "source_metadata_conflict",
          is_official_government_form: false,
          is_synthetic_sample: false,
          human_review_required: true,
          source_conflict_flag: true,
          statutory_limitation_notice: "STATUTORY LIMITATION NOTICE: DOC_043 retains an unverified source metadata conflict. Claims derived from this document must not be presented as standalone statutory entitlements. Mandatory human verification by UIDAI Regional Office is required.",
          related_procedures: [],
          checklists: [],
          citations: [],
        }),
      });
    });
  });

  test("Citizen opens document repository, filters by category, inspects details and checklist", async ({ page }) => {
    // 1. Set simulated token in localStorage
    const token = "test_token_:cit_e2e_123:citizen@example.com:Aarav Sharma";
    await page.addInitScript((tok) => {
      try {
        localStorage.setItem("convelina_test_token", tok);
      } catch {}
    }, token);

    // 2. Navigate to Citizen Document Repository
    await page.goto("/app/forms");

    // 3. Verify Repository Header and Category Tabs
    await expect(page.locator("h1:has-text('Document Repository & Correction Guidance')")).toBeVisible({ timeout: 15000 });
    await expect(page.locator("button:has-text('All Documents')")).toBeVisible();
    await expect(page.locator("button:has-text('Aadhaar Card')")).toBeVisible();
    await expect(page.locator("button:has-text('PAN Card')")).toBeVisible();
    await expect(page.locator("button:has-text('Passport')")).toBeVisible();
    await expect(page.locator("button:has-text('Class 10 Certificate')")).toBeVisible();
    await expect(page.locator("button:has-text('Class 12 Certificate')")).toBeVisible();
    await expect(page.locator("button:has-text('EPF/UAN Records')")).toBeVisible();

    // 4. Test Category Filter (PAN Card)
    const panTab = page.locator("button:has-text('PAN Card')").first();
    await panTab.click();
    await page.waitForTimeout(500);

    // 5. Test Search Bar (DOC_036)
    const searchInput = page.locator("input[placeholder*='Search by document ID']").first();
    await searchInput.fill("DOC_036");
    const searchBtn = page.locator("button:has-text('Search')").first();
    await searchBtn.click();
    await page.waitForTimeout(500);

    // 6. Inspect Rendered Document Card
    const docCard = page.locator("div:has-text('DOC_036')").first();
    await expect(docCard).toBeVisible({ timeout: 10000 });
    await expect(docCard.locator("text=Income Tax Department").first()).toBeVisible();

    // 7. Open Document Details View
    const detailsLink = docCard.locator("a:has-text('View Details & Checklist')").first();
    await detailsLink.click();

    // 8. Verify Dedicated Document Detail View (/app/forms/DOC_036)
    await expect(page).toHaveURL(/.*\/app\/forms\/DOC_036/);
    await expect(page.locator("h1")).toBeVisible({ timeout: 10000 });

    // 9. Verify All Required Detail Sections
    await expect(page.locator("h2:has-text('What is this document used for?')")).toBeVisible();
    await expect(page.locator("h2:has-text('Who should use it?')")).toBeVisible();
    await expect(page.locator("h2:has-text('Required Supporting Documents Checklist')")).toBeVisible();
    await expect(page.locator("h2:has-text('Original Document Asset')")).toBeVisible();
    await expect(page.locator("h2:has-text('Source Citations & Statutory Limitations')")).toBeVisible();

    // 10. Test Interactive Checklist Item Toggle
    const checklistCheckbox = page.locator("input[type='checkbox']").first();
    if (await checklistCheckbox.isVisible()) {
      await checklistCheckbox.click();
      await expect(checklistCheckbox).toBeChecked();
    }

    // 11. Test DOC_043 Invariant & Statutory Limitation Notice
    await page.goto("/app/forms/DOC_043");
    await expect(page.locator("text=STATUTORY LIMITATION NOTICE").first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=DOC_043 retains an unverified source metadata conflict").first()).toBeVisible();
  });
});

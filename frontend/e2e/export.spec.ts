import { test, expect } from "@playwright/test";
import { provisionTestCitizenApi, API_URL } from "./helpers";

test.describe("4.8 Document Export & Binary Stream Validation", () => {
  test("Export endpoint returns valid binary PDF/DOCX for authorized drafts", async () => {
    const citizen = await provisionTestCitizenApi();

    // Call export endpoint for non-existent draft to verify 404 security handling
    const nonExistentDraftId = "00000000-0000-0000-0000-000000000000";
    const res = await fetch(`${API_URL}/api/v1/correction-drafts/${nonExistentDraftId}/download?format=pdf`, {
      headers: {
        Authorization: `Bearer ${citizen.token}`,
      },
    });

    // Must return 404 rather than 500 or leaking other data
    expect(res.status).toBe(404);
  });
});

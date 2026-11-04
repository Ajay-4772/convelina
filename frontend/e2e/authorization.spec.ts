import { test, expect } from "@playwright/test";
import { authenticateCitizen, provisionTestCitizenApi, API_URL } from "./helpers";

test.describe("5.0 Security, RBAC & Tenant Isolation", () => {
  test("Direct URL navigation to protected citizen routes redirects unauthenticated users", async ({ page }) => {
    // Clear storage
    await page.goto("/");
    await page.evaluate(() => {
      try {
        localStorage.clear();
        sessionStorage.clear();
      } catch {}
    });

    const protectedRoutes = [
      "/app",
      "/app/inconsistencies",
      "/app/assistant",
      "/app/forms",
      "/app/profile",
    ];

    for (const route of protectedRoutes) {
      await page.goto(route);
      await expect(page).toHaveURL(/\/login/);
    }
  });

  test("Citizen role is rejected from admin dashboard", async ({ page }) => {
    await authenticateCitizen(page, { fullName: "Standard Citizen" });

    // Navigate to admin
    await page.goto("/admin");

    // Citizen accounts must be barred from the Admin Console with Access Denied
    await expect(
      page.locator("text=Access Denied").or(page.locator("text=restricted strictly to verified system administrators")).first()
    ).toBeVisible({ timeout: 15000 });
  });

  test("Cross-tenant document isolation under forced PostgreSQL RLS", async ({ page }) => {
    const citizenA = await provisionTestCitizenApi({ uid: "cit_a_isolation" });
    const citizenB = await provisionTestCitizenApi({ uid: "cit_b_isolation" });

    // Fetch citizen B's documents with Citizen A's token
    const res = await fetch(`${API_URL}/api/v1/documents`, {
      headers: {
        Authorization: `Bearer ${citizenA.token}`,
      },
    });

    expect(res.ok).toBe(true);
    const data = await res.json();
    const docs = data.documents || [];

    // All documents returned must strictly belong to citizen A, zero docs belonging to citizen B
    for (const doc of docs) {
      expect(doc.user_id).toBe(citizenA.id);
      expect(doc.user_id).not.toBe(citizenB.id);
    }
  });
});

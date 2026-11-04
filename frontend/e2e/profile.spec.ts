import { test, expect } from "@playwright/test";
import { authenticateCitizen } from "./helpers";

test.describe("4.2 Citizen Profile & Consent Management", () => {
  test("Profile loads demographic data and allows updating information", async ({ page }) => {
    const citizen = await authenticateCitizen(page, {
      fullName: "Ananya Deshmukh",
      email: "ananya_profile_e2e@example.com",
    });

    await page.goto("/app/profile");
    await expect(page).toHaveTitle(/CONVELINA/i);

    // Verify citizen name is displayed
    await expect(page.locator("text=Ananya Deshmukh").first()).toBeVisible({ timeout: 15000 });
    await expect(page.locator(`text=${citizen.email}`).first()).toBeVisible();

    // Verify security & credentials or personal info section
    await expect(page.locator("h2:has-text('Personal Information')").first()).toBeVisible();
    await expect(page.locator("h2:has-text('Security & Credentials')").first()).toBeVisible();

    // Click Edit Profile
    const editBtn = page.locator("button:has-text('Edit Profile')");
    await expect(editBtn).toBeVisible();
    await editBtn.click();

    // Update Address field
    const addressInput = page.locator("textarea").first();
    await addressInput.fill("Flat 402, Sunshine Apts, MG Road, Pune - 411001");

    // Save Changes
    const saveBtn = page.locator("button:has-text('Save Changes')");
    await expect(saveBtn).toBeVisible();
    await saveBtn.click();

    // Verify success banner appears
    await expect(page.locator("text=Profile updated successfully").first()).toBeVisible({ timeout: 10000 });
  });

  test("Account deletion modal displays privacy safeguards", async ({ page }) => {
    await authenticateCitizen(page);
    await page.goto("/app/profile");

    // Check for Danger Zone / Delete Account trigger
    const deleteButton = page.locator("button:has-text('Delete Account')");
    await expect(deleteButton).toBeVisible({ timeout: 15000 });
    await deleteButton.click();

    // Verify modal opens with warning about data destruction
    await expect(
      page.locator("h3:has-text('Permanently delete account?')").first()
    ).toBeVisible({ timeout: 10000 });

    // Dismiss modal safely
    const cancelBtn = page.locator("button:has-text('Cancel')");
    await cancelBtn.click();
    await expect(page.locator("h3:has-text('Permanently delete account?')")).not.toBeVisible();
  });
});

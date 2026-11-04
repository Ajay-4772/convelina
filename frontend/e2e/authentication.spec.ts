import { test, expect } from "@playwright/test";

test.describe("4.1 Authentication & Role Scoping", () => {
  test("Registration page validation rules", async ({ page }) => {
    await page.goto("/signup");
    await expect(page).toHaveTitle(/CONVELINA/i);

    // Form inputs: exactly one email, two passwords, one checkbox, one submit
    const emailInput = page.locator('input[type="email"]');
    const passwordInput = page.locator('input[type="password"]').first();
    const confirmInput = page.locator('input[type="password"]').nth(1);
    const submitButton = page.locator('button[type="submit"]');

    await expect(emailInput).toBeVisible();
    await expect(passwordInput).toBeVisible();
    await expect(confirmInput).toBeVisible();
    await expect(submitButton).toBeVisible();

    // 1. Submit empty form
    await submitButton.click();
    await expect(page.locator("text=Please enter your official email address").first()).toBeVisible();

    // 2. Submit with short password
    await emailInput.fill("test_citizen@example.com");
    await passwordInput.fill("123");
    await confirmInput.fill("123");
    await submitButton.click();
    await expect(page.locator("text=Password must be at least 6 characters in length").first()).toBeVisible();

    // 3. Submit with mismatched passwords
    await passwordInput.fill("securePassword123");
    await confirmInput.fill("differentPassword456");
    await submitButton.click();
    await expect(page.locator("text=Passwords do not match. Please verify.").first()).toBeVisible();

    // 4. Submit without agreeing to terms
    await confirmInput.fill("securePassword123");
    await submitButton.click();
    await expect(page.locator("text=You must acknowledge the terms and data privacy policy").first()).toBeVisible();
  });

  test("Email verification page interface", async ({ page }) => {
    const testEmail = "citizen_verify_test@example.com";
    await page.goto(`/verify-email?email=${encodeURIComponent(testEmail)}`);

    // Verify email and verification heading are rendered
    await expect(page.locator(`text=${testEmail}`).first()).toBeVisible();
    await expect(page.locator("h1:has-text('Verify your email')").first()).toBeVisible();

    // Verify OTP input box exists
    const otpInput = page.locator('input[type="text"]').first();
    await expect(otpInput).toBeVisible();

    // Verify resend code button exists
    const resendButton = page.locator("button").filter({ hasText: /Resend/i });
    await expect(resendButton).toBeVisible();
  });

  test("Citizen login validation and flow", async ({ page }) => {
    await page.goto("/login");

    const emailInput = page.locator('input[type="email"]');
    const passwordInput = page.locator('input[type="password"]');
    const submitButton = page.locator('button[type="submit"]');

    // 1. Submit without email
    await submitButton.click();
    await expect(page.locator("text=Please enter your email address").first()).toBeVisible();

    // 2. Submit with email but no password
    await emailInput.fill("citizen_demo@example.com");
    await submitButton.click();
    await expect(page.locator("text=Please enter your password").first()).toBeVisible();

    // 3. Submit valid test credentials
    await passwordInput.fill("securePassword123");
    await submitButton.click();

    // Should navigate away from login to /app or /setup-profile
    await expect(page).not.toHaveURL(/\/login$/);
  });

  test("Protected route redirects unauthenticated users", async ({ page }) => {
    // Navigate directly to protected citizen app
    await page.goto("/app");
    // Should redirect to login
    await expect(page).toHaveURL(/\/login/);
  });
});

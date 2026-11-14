import { test, expect } from "@playwright/test";
import { authenticateCitizen, API_URL } from "./helpers";

test.describe("P3A.1 Dynamic Conversation Routing & History Navigation", () => {
  test("Dynamic conversation route loads existing conversation and messages on direct URL access", async ({
    page,
  }) => {
    test.setTimeout(120000);
    // 1. Provision authenticated citizen
    const citizen = await authenticateCitizen(page);

    // 2. Create conversation via backend API under citizen's token
    const convRes = await fetch(`${API_URL}/api/v1/assistant/conversations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${citizen.token}`,
      },
      body: JSON.stringify({
        title: "EPFO Joint Declaration Inquiry",
        response_language: "en",
      }),
    });
    expect(convRes.ok).toBeTruthy();
    const conv = await convRes.json();
    const convId = conv.id;

    // 3. Post a message to this conversation
    const chatRes = await fetch(`${API_URL}/api/v1/assistant/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${citizen.token}`,
      },
      body: JSON.stringify({
        message: "How do I correct my father's name in EPFO records?",
        conversation_id: convId,
      }),
    });
    expect(chatRes.ok).toBeTruthy();

    // 4. Navigate directly to the dynamic route: /app/assistant/[conversationId]
    await page.goto(`/app/assistant/${convId}`);

    // Verify page does NOT render a 404 error
    await expect(page.locator("text=404").or(page.locator("text=This page could not be found"))).toHaveCount(0);

    // Verify conversation title appears in header or sidebar
    await expect(page.locator(`text=${conv.title}`).first()).toBeVisible({ timeout: 15000 });

    // Verify user question is rendered in the chat thread
    await expect(page.locator("text=How do I correct my father's name in EPFO records?")).toBeVisible({
      timeout: 15000,
    });

    // 5. Refresh the browser and verify messages reload without 404
    await page.reload();
    await expect(page.locator("text=404")).toHaveCount(0);
    await expect(page.locator("text=How do I correct my father's name in EPFO records?")).toBeVisible({
      timeout: 15000,
    });

    // 6. Navigate to New Inquiry via Sidebar button (+ New Inquiry)
    const newInquiryBtn = page.locator("button:has-text('New Inquiry')").or(page.locator("button:has-text('New')")).first();
    await newInquiryBtn.click();

    // URL should change to /app/assistant
    await expect(page).toHaveURL(/\/app\/assistant$/);

    // Canvas should display welcome state
    await expect(page.locator("text=Good").first()).toBeVisible({ timeout: 10000 });

    // 7. Test Browser Back navigation
    await page.goBack();

    // URL should revert to /app/assistant/[convId]
    await expect(page).toHaveURL(new RegExp(`/app/assistant/${convId}`));

    // Message should reappear
    await expect(page.locator("text=How do I correct my father's name in EPFO records?")).toBeVisible({
      timeout: 15000,
    });

    // 8. Test Browser Forward navigation
    await page.goForward();
    await expect(page).toHaveURL(/\/app\/assistant$/);
    await expect(page.locator("text=Good").first()).toBeVisible({ timeout: 10000 });
  });

  test("Unauthorized or invalid conversation ID shows graceful error and blocks cross-tenant leakage", async ({
    page,
  }) => {
    test.setTimeout(120000);
    // 1. Provision Citizen A and create a confidential conversation
    const citizenA = await authenticateCitizen(page, { fullName: "Citizen Alpha" });
    const convResA = await fetch(`${API_URL}/api/v1/assistant/conversations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${citizenA.token}`,
      },
      body: JSON.stringify({
        title: "Confidential Alpha Passport Inquiry",
        response_language: "en",
      }),
    });
    expect(convResA.ok).toBeTruthy();
    const convA = await convResA.json();

    await fetch(`${API_URL}/api/v1/assistant/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${citizenA.token}`,
      },
      body: JSON.stringify({
        message: "Secret citizen Alpha passport number Z9876543 details.",
        conversation_id: convA.id,
      }),
    });

    // 2. Provision Citizen B and authenticate in browser
    const citizenB = await authenticateCitizen(page, { fullName: "Citizen Beta" });

    // 3. Citizen B attempts to access Citizen A's conversation URL
    await page.goto(`/app/assistant/${convA.id}`);

    // Verify 404 Next.js page is not shown, but access denied / not found alert is shown
    await expect(page.locator("text=This page could not be found")).toHaveCount(0);
    await expect(
      page.locator("text=Conversation not found or access denied").or(page.locator("text=Failed to load conversation"))
    ).toBeVisible({ timeout: 15000 });

    // Verify Citizen A's private text is NOT leaked in Citizen B's view
    await expect(page.locator("text=Secret citizen Alpha passport number")).toHaveCount(0);
    await expect(page.locator("text=Confidential Alpha Passport Inquiry")).toHaveCount(0);

    // 4. Direct navigation to completely invalid UUID
    await page.goto("/app/assistant/00000000-0000-0000-0000-000000000000");
    await expect(
      page.locator("text=Conversation not found or access denied").or(page.locator("text=Failed to load conversation"))
    ).toBeVisible({ timeout: 15000 });
  });
});

import { test, expect } from "@playwright/test";
import { authenticateCitizen, API_URL } from "./helpers";

test.describe("P3A.2 Conversation Lifecycle & Persistence Verification", () => {
  test("Workflows 1-4: Create conversation, send first message, receive response, and send follow-up messages", async ({
    page,
  }) => {
    test.setTimeout(120000);
    // Authenticate citizen
    await authenticateCitizen(page, { fullName: "Rohan Verma" });

    // 1. Navigate to /app/assistant (empty state)
    await page.goto("/app/assistant");
    await expect(page.locator("main").locator("text=Good").first()).toBeVisible({ timeout: 15000 });

    // 2. Type first inquiry into hero composer
    const textarea = page.locator("main textarea").first();
    await expect(textarea).toBeVisible();
    await textarea.fill("How do I update the date of birth on my PAN card?");

    // 3. Submit first message
    const sendBtn = page.locator("main button[aria-label='Send message']").first();
    await sendBtn.click();

    // 4. Verify URL transitions to dynamic conversation route (/app/assistant/[uuid])
    await expect(page).toHaveURL(/\/app\/assistant\/[0-9a-fA-F-]+$/, { timeout: 20000 });

    // 5. Verify user message is visible in thread (Workflow 2)
    await expect(
      page.locator("main").locator("text=How do I update the date of birth on my PAN card?").first()
    ).toBeVisible({ timeout: 15000 });

    // 6. Verify assistant response arrives (Workflow 3)
    await expect(
      page.locator("main").locator("text=AUTOMATED COMPARISON RESULT").first()
    ).toBeVisible({ timeout: 30000 });

    // 7. Send follow-up message in active conversation (pill composer) (Workflow 4)
    const followUpTextarea = page.locator("main textarea").first();
    await followUpTextarea.fill("What official form is required for this correction?");
    await page.locator("main button[aria-label='Send message']").first().click();

    // 8. Verify follow-up message appears in the conversation thread
    await expect(
      page.locator("main").locator("text=What official form is required for this correction?").first()
    ).toBeVisible({ timeout: 15000 });

    // 9. Verify second assistant response arrives
    await expect(
      page.locator("main").locator("text=AUTOMATED COMPARISON RESULT").nth(1)
    ).toBeVisible({ timeout: 30000 });
  });

  test("Workflows 5-7: Browser reload, persistent history restoration, and direct URL access", async ({
    page,
  }) => {
    test.setTimeout(120000);
    const citizen = await authenticateCitizen(page, { fullName: "Priya Nair" });

    // 1. Create conversation with messages via backend API
    const convRes = await fetch(`${API_URL}/api/v1/assistant/conversations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${citizen.token}`,
      },
      body: JSON.stringify({
        title: "Aadhaar Name Mismatch Inquiry",
        response_language: "en",
      }),
    });
    expect(convRes.ok).toBeTruthy();
    const conv = await convRes.json();
    const convId = conv.id;

    // Send first message
    const msg1Res = await fetch(`${API_URL}/api/v1/assistant/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${citizen.token}`,
      },
      body: JSON.stringify({
        message: "My name on Aadhaar is misspelled. How can I fix it?",
        conversation_id: convId,
      }),
    });
    expect(msg1Res.ok).toBeTruthy();

    // 2. Workflow 7: Open existing conversation directly via its URL
    await page.goto(`/app/assistant/${convId}`);

    // Verify conversation title appears in sidebar or header
    await expect(page.locator("aside").locator(`text=${conv.title}`).first()).toBeVisible({ timeout: 15000 });

    // Verify message content is rendered from PostgreSQL database (Workflow 6)
    await expect(
      page.locator("main").locator("text=My name on Aadhaar is misspelled. How can I fix it?").first()
    ).toBeVisible({ timeout: 15000 });

    // 3. Workflow 5: Refresh browser
    await page.reload();

    // 4. Workflow 6: Verify complete conversation is restored after refresh
    await expect(page.locator("text=404")).toHaveCount(0);
    await expect(
      page.locator("main").locator("text=My name on Aadhaar is misspelled. How can I fix it?").first()
    ).toBeVisible({ timeout: 15000 });
    await expect(page.locator("aside").locator(`text=${conv.title}`).first()).toBeVisible({ timeout: 15000 });
  });

  test("Workflows 8-10: Multi-conversation switching, rename via modal, and delete via modal", async ({
    page,
  }) => {
    test.setTimeout(120000);
    const citizen = await authenticateCitizen(page, { fullName: "Vikram Mehta" });

    // 1. Create two distinct conversations via API
    const conv1Res = await fetch(`${API_URL}/api/v1/assistant/conversations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${citizen.token}`,
      },
      body: JSON.stringify({
        title: "Passport Surname Correction",
        response_language: "en",
      }),
    });
    const conv1 = await conv1Res.json();

    const conv2Res = await fetch(`${API_URL}/api/v1/assistant/conversations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${citizen.token}`,
      },
      body: JSON.stringify({
        title: "EPFO Joint Declaration Request",
        response_language: "en",
      }),
    });
    const conv2 = await conv2Res.json();

    // Seed a message in conv1
    await fetch(`${API_URL}/api/v1/assistant/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${citizen.token}`,
      },
      body: JSON.stringify({
        message: "Passport surname verification checklist",
        conversation_id: conv1.id,
      }),
    });

    // 2. Open /app/assistant
    await page.goto("/app/assistant");

    // Verify both conversations are listed in sidebar
    await expect(page.locator("aside").locator(`text=${conv1.title}`).first()).toBeVisible({ timeout: 15000 });
    await expect(page.locator("aside").locator(`text=${conv2.title}`).first()).toBeVisible({ timeout: 15000 });

    // 3. Workflow 8: Switch to Conversation 1
    await page.locator("aside").locator(`text=${conv1.title}`).first().click();
    await expect(page).toHaveURL(new RegExp(`/app/assistant/${conv1.id}`));
    await expect(
      page.locator("main").locator("text=Passport surname verification checklist").first()
    ).toBeVisible({ timeout: 15000 });

    // Switch to Conversation 2
    await page.locator("aside").locator(`text=${conv2.title}`).first().click();
    await expect(page).toHaveURL(new RegExp(`/app/assistant/${conv2.id}`));

    // 4. Workflow 9: Rename Conversation 1 via modal
    const conv1Row = page.locator("aside").locator(".group", { hasText: conv1.title }).first();
    await conv1Row.hover();
    const renameBtn = conv1Row.locator("button[aria-label='Rename chat']");
    await renameBtn.click({ force: true });

    // Verify rename modal appears
    await expect(page.locator("text=Rename Inquiry Session")).toBeVisible();
    const renameInput = page.locator("div.fixed input[type='text']").first();
    await renameInput.fill("Passport Surname Urgent Correction");
    await page.locator("div.fixed button:has-text('Save')").click();

    // Verify new title is reflected in sidebar
    await expect(page.locator("aside").locator("text=Passport Surname Urgent Correction").first()).toBeVisible({
      timeout: 10000,
    });

    // 5. Workflow 10: Delete Conversation 2 via modal
    const conv2Row = page.locator("aside").locator(".group", { hasText: conv2.title }).first();
    await conv2Row.hover();
    const deleteBtn = conv2Row.locator("button[aria-label='Delete chat']");
    await deleteBtn.click({ force: true });

    // Verify delete confirmation modal
    await expect(page.locator("text=Delete inquiry session?")).toBeVisible();
    await page.locator("div.fixed button:has-text('Delete')").click();

    // Verify Conversation 2 is removed from sidebar
    await expect(page.locator("aside").locator(`text=${conv2.title}`)).toHaveCount(0, { timeout: 10000 });
  });

  test("Workflow 11: Search conversations via Ctrl+K / Search Modal", async ({ page }) => {
    test.setTimeout(120000);
    const citizen = await authenticateCitizen(page, { fullName: "Sunita Rao" });

    // Create a searchable conversation
    const convRes = await fetch(`${API_URL}/api/v1/assistant/conversations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${citizen.token}`,
      },
      body: JSON.stringify({
        title: "Tatkal Passport Processing Guidelines",
        response_language: "en",
      }),
    });
    const conv = await convRes.json();

    await page.goto("/app/assistant");

    // Open search modal via search button in sidebar
    const searchBtn = page.locator("aside button[aria-label='Search chat history']").first();
    await expect(searchBtn).toBeVisible({ timeout: 15000 });
    await searchBtn.click();

    // Verify search modal opened
    const searchInput = page.locator(
      "input[placeholder='Search inquiries, message notes, or statutory questions...']"
    );
    await expect(searchInput).toBeVisible({ timeout: 5000 });

    // Type query
    await searchInput.fill("Tatkal");

    // Wait for search result to appear
    const resultItem = page.locator("div.fixed").locator("text=Tatkal Passport Processing Guidelines").first();
    await expect(resultItem).toBeVisible({ timeout: 10000 });

    // Click search result to navigate to conversation
    await resultItem.click();

    // Modal should close and URL should be the selected conversation
    await expect(searchInput).not.toBeVisible();
    await expect(page).toHaveURL(new RegExp(`/app/assistant/${conv.id}`));
  });

  test("Workflow 12: Browser Back and Forward navigation", async ({ page }) => {
    test.setTimeout(120000);
    const citizen = await authenticateCitizen(page, { fullName: "Deepak Patel" });

    // Create conversation via API
    const convRes = await fetch(`${API_URL}/api/v1/assistant/conversations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${citizen.token}`,
      },
      body: JSON.stringify({
        title: "10th Certificate Board Verification",
        response_language: "en",
      }),
    });
    const conv = await convRes.json();

    // Start on /app/assistant
    await page.goto("/app/assistant");
    await expect(page.locator("main").locator("text=Good").first()).toBeVisible({ timeout: 15000 });

    // Navigate into conversation
    await page.locator("aside").locator(`text=${conv.title}`).first().click();
    await expect(page).toHaveURL(new RegExp(`/app/assistant/${conv.id}`));

    // Click New Chat button
    const newChatBtn = page.locator("aside button:has-text('New Chat')").first();
    await newChatBtn.click();
    await expect(page).toHaveURL(/\/app\/assistant$/);
    await expect(page.locator("main").locator("text=Good").first()).toBeVisible({ timeout: 10000 });

    // Browser Back -> returns to conversation
    await page.goBack();
    await expect(page).toHaveURL(new RegExp(`/app/assistant/${conv.id}`));
    await expect(page.locator("aside").locator(`text=${conv.title}`).first()).toBeVisible({ timeout: 10000 });

    // Browser Forward -> returns to new inquiry
    await page.goForward();
    await expect(page).toHaveURL(/\/app\/assistant$/);
    await expect(page.locator("main").locator("text=Good").first()).toBeVisible({ timeout: 10000 });
  });

  test("Workflow 13: Handle non-existent or deleted conversation gracefully", async ({ page }) => {
    test.setTimeout(120000);
    await authenticateCitizen(page, { fullName: "Kavita Reddy" });

    // Navigate to a non-existent UUID
    const nonExistentUuid = "00000000-0000-0000-0000-000000000000";
    await page.goto(`/app/assistant/${nonExistentUuid}`);

    // Verify graceful error banner is displayed
    await expect(
      page.locator("text=Conversation not found or access denied.")
    ).toBeVisible({ timeout: 15000 });

    // Verify no unhandled Next.js crash
    await expect(page.locator("text=Application error")).toHaveCount(0);
    await expect(page.locator("text=Internal Server Error")).toHaveCount(0);
  });

  test("Workflow 14: Unavailable backend restores composer text and shows error banner", async ({
    page,
  }) => {
    test.setTimeout(120000);
    await authenticateCitizen(page, { fullName: "Ananya Deshmukh" });

    await page.goto("/app/assistant");
    await expect(page.locator("main").locator("text=Good").first()).toBeVisible({ timeout: 15000 });

    // Intercept chat endpoint to simulate backend 503 outage
    await page.route("**/api/v1/assistant/chat", async (route) => {
      await route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Assistant service temporarily unavailable for maintenance." }),
      });
    });

    const textarea = page.locator("main textarea").first();
    const testQuery = "Draft an urgent name correction application to UIDAI.";
    await textarea.fill(testQuery);

    // Click send
    await page.locator("main button[aria-label='Send message']").first().click();

    // Verify error banner appears
    await expect(page.locator("text=Assistant service temporarily unavailable")).toBeVisible({
      timeout: 10000,
    });

    // Verify the query text is restored in the textarea so user doesn't lose work
    await expect(textarea).toHaveValue(testQuery);

    // Verify no persistent assistant reply bubble was rendered
    await expect(page.locator("text=AUTOMATED COMPARISON RESULT")).toHaveCount(0);
  });

  test("Workflow 15: Rapid submission / double-submit duplicate prevention", async ({ page }) => {
    test.setTimeout(120000);
    await authenticateCitizen(page, { fullName: "Arjun Nair" });

    await page.goto("/app/assistant");
    await expect(page.locator("main").locator("text=Good").first()).toBeVisible({ timeout: 15000 });

    let requestCount = 0;
    // Intercept /api/v1/assistant/chat to count requests
    await page.route("**/api/v1/assistant/chat", async (route) => {
      requestCount++;
      // Add slight delay to simulate network latency
      await new Promise((resolve) => setTimeout(resolve, 800));
      await route.continue();
    });

    const textarea = page.locator("main textarea").first();
    await textarea.fill("Verify discrepancy between PAN and Aadhaar date of birth");

    // Click send twice in rapid succession
    const sendBtn = page.locator("main button[aria-label='Send message']").first();
    await Promise.all([
      sendBtn.click({ clickCount: 1 }),
      sendBtn.click({ clickCount: 1 }),
    ]);

    // Wait for the response
    await expect(page).toHaveURL(/\/app\/assistant\/[0-9a-fA-F-]+$/, { timeout: 30000 });

    // Verify only ONE request was dispatched
    expect(requestCount).toBe(1);
  });

  test("Security: Cross-tenant conversation isolation under forced PostgreSQL RLS", async ({
    page,
    browser,
  }) => {
    test.setTimeout(120000);
    // 1. Citizen A creates a private conversation
    const citizenA = await authenticateCitizen(page, { fullName: "Citizen Alpha" });
    const convResA = await fetch(`${API_URL}/api/v1/assistant/conversations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${citizenA.token}`,
      },
      body: JSON.stringify({
        title: "Confidential Tax Assessment Inquiry",
        response_language: "en",
      }),
    });
    const convA = await convResA.json();

    // Seed private message
    await fetch(`${API_URL}/api/v1/assistant/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${citizenA.token}`,
      },
      body: JSON.stringify({
        message: "Secret income tax rectification data for Citizen A",
        conversation_id: convA.id,
      }),
    });

    // 2. Citizen B creates an isolated session in a separate browser context
    const contextB = await browser.newContext();
    const pageB = await contextB.newPage();
    const citizenB = await authenticateCitizen(pageB, { fullName: "Citizen Beta" });

    // Citizen B attempts direct URL access to Citizen A's conversation
    await pageB.goto(`/app/assistant/${convA.id}`);

    // Verify Citizen B receives graceful access denied / not found
    await expect(
      pageB.locator("text=Conversation not found or access denied.")
    ).toBeVisible({ timeout: 15000 });

    // Verify Citizen A's private message is NEVER rendered to Citizen B
    await expect(
      pageB.locator("text=Secret income tax rectification data for Citizen A")
    ).toHaveCount(0);

    // Verify backend rejects Citizen B from modifying Citizen A's conversation
    const patchRes = await fetch(`${API_URL}/api/v1/assistant/conversations/${convA.id}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${citizenB.token}`,
      },
      body: JSON.stringify({ title: "Hacked by Citizen B" }),
    });
    expect(patchRes.status).toBe(404);

    // Verify backend rejects Citizen B from deleting Citizen A's conversation
    const deleteRes = await fetch(`${API_URL}/api/v1/assistant/conversations/${convA.id}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${citizenB.token}`,
      },
    });
    expect(deleteRes.status).toBe(404);

    await contextB.close();
  });
});

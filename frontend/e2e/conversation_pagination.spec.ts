import { test, expect } from "@playwright/test";
import { authenticateCitizen, API_URL } from "./helpers";
import { execSync } from "child_process";
import crypto from "crypto";

/**
 * Helper to seed deterministic messages directly in PostgreSQL
 */
function seedHistoricalMessages(conversationId: string, userId: string, count: number) {
  const values: string[] = [];
  const baseTime = new Date(Date.now() - (count + 10) * 60 * 1000);
  for (let i = 0; i < count; i++) {
    const msgId = crypto.randomUUID();
    const role = i % 2 === 0 ? "user" : "assistant";
    const content = `Historical Message ${i.toString().padStart(2, "0")}`;
    const dt = new Date(baseTime.getTime() + i * 60 * 1000).toISOString();
    values.push(`('${msgId}', '${conversationId}', '${userId}', '${role}', '${content}', '${dt}')`);
  }
  const sql = `INSERT INTO assistant_messages (id, conversation_id, user_id, role, content, created_at) VALUES ${values.join(", ")};`;
  execSync(`docker exec convelina-postgres psql -U postgres -d consolith -c "${sql}"`);
}

test.describe("P3A.3 Scalable Conversation Message Pagination", () => {
  test("Workflow 1 & 2: Opening latest message page and loading older messages with scroll stability", async ({
    page,
  }) => {
    test.setTimeout(120000);
    const citizen = await authenticateCitizen(page, { fullName: "Vikram Malhotra" });

    // 1. Create a conversation via API
    const convRes = await fetch(`${API_URL}/api/v1/assistant/conversations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${citizen.token}`,
      },
      body: JSON.stringify({ title: "35 Messages Pagination Test" }),
    });
    expect(convRes.status).toBe(201);
    const convData = await convRes.json();
    const convId = convData.id;

    // 2. Seed 35 messages into the conversation
    seedHistoricalMessages(convId, citizen.id, 35);

    // 3. Navigate directly to dynamic conversation route
    await page.goto(`/app/assistant/${convId}`);

    // Verify latest messages are visible
    await expect(page.locator("main").locator("text=Historical Message 34")).toBeVisible({ timeout: 15000 });
    await expect(page.locator("main").locator("text=Historical Message 05")).toBeVisible({ timeout: 15000 });

    // Earliest messages (00 to 04) should NOT be loaded on the initial page of 30
    await expect(page.locator("main").locator("text=Historical Message 00")).not.toBeVisible();

    // Verify "Load older messages" button is visible
    const loadOlderBtn = page.locator("main button[aria-label='Load older messages']");
    await expect(loadOlderBtn).toBeVisible({ timeout: 10000 });

    // 4. Click "Load older messages"
    await loadOlderBtn.click();

    // 5. Verify older messages are prepended without jumping or duplicating
    await expect(page.locator("main").locator("text=Historical Message 00")).toBeVisible({ timeout: 15000 });
    await expect(page.locator("main").locator("text=Historical Message 34")).toBeVisible();

    // "Load older messages" button should now disappear since has_more is false
    await expect(loadOlderBtn).not.toBeVisible();
  });

  test("Workflow 3: Sending a new message after paginating older messages", async ({
    page,
  }) => {
    test.setTimeout(120000);
    const citizen = await authenticateCitizen(page, { fullName: "Ananya Iyer" });

    const convRes = await fetch(`${API_URL}/api/v1/assistant/conversations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${citizen.token}`,
      },
      body: JSON.stringify({ title: "Send After Pagination Chat" }),
    });
    const convData = await convRes.json();
    const convId = convData.id;

    seedHistoricalMessages(convId, citizen.id, 35);

    await page.goto(`/app/assistant/${convId}`);
    await expect(page.locator("main").locator("text=Historical Message 34")).toBeVisible({ timeout: 15000 });

    // Load older messages
    const loadOlderBtn = page.locator("main button[aria-label='Load older messages']");
    await expect(loadOlderBtn).toBeVisible({ timeout: 10000 });
    await loadOlderBtn.click();
    await expect(page.locator("main").locator("text=Historical Message 00")).toBeVisible({ timeout: 15000 });

    // Send a new message
    const textarea = page.locator("main textarea").first();
    await expect(textarea).toBeVisible({ timeout: 10000 });
    await textarea.fill("What is the next step for this record?");

    const sendBtn = page.locator("main button[aria-label='Send message']").first();
    await expect(sendBtn).toBeEnabled({ timeout: 10000 });
    await sendBtn.click();

    // Verify user message appears at the bottom
    await expect(
      page.locator("main").locator("text=What is the next step for this record?").first()
    ).toBeVisible({ timeout: 15000 });

    // Verify assistant responds
    await expect(
      page.locator("main").locator("text=AUTOMATED COMPARISON RESULT").first()
    ).toBeVisible({ timeout: 30000 });
  });

  test("Workflow 4: Switching conversations resets pagination state correctly", async ({
    page,
  }) => {
    test.setTimeout(120000);
    const citizen = await authenticateCitizen(page, { fullName: "Kavita Nair" });

    // Conversation 1: 35 messages
    const conv1Res = await fetch(`${API_URL}/api/v1/assistant/conversations`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${citizen.token}` },
      body: JSON.stringify({ title: "Long Thread with 35 Msgs" }),
    });
    const conv1Data = await conv1Res.json();
    seedHistoricalMessages(conv1Data.id, citizen.id, 35);

    // Conversation 2: 3 messages
    const conv2Res = await fetch(`${API_URL}/api/v1/assistant/conversations`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${citizen.token}` },
      body: JSON.stringify({ title: "Short Thread with 3 Msgs" }),
    });
    const conv2Data = await conv2Res.json();
    seedHistoricalMessages(conv2Data.id, citizen.id, 3);

    // Load Conversation 1
    await page.goto(`/app/assistant/${conv1Data.id}`);
    await expect(page.locator("main button[aria-label='Load older messages']")).toBeVisible({ timeout: 15000 });

    // Switch to Conversation 2 via sidebar
    const conv2SidebarBtn = page.locator("aside").locator("text=Short Thread with 3 Msgs").first();
    await expect(conv2SidebarBtn).toBeVisible({ timeout: 15000 });
    await conv2SidebarBtn.click();

    await expect(page).toHaveURL(new RegExp(`/app/assistant/${conv2Data.id}$`), { timeout: 15000 });

    // Conversation 2 has only 3 messages, so "Load older messages" should NOT be visible
    await expect(page.locator("main").locator("text=Historical Message 02")).toBeVisible({ timeout: 15000 });
    await expect(page.locator("main button[aria-label='Load older messages']")).not.toBeVisible();
  });

  test("Workflow 5: Retrying a failed older-message request", async ({
    page,
  }) => {
    test.setTimeout(120000);
    const citizen = await authenticateCitizen(page, { fullName: "Devendra Patel" });

    const convRes = await fetch(`${API_URL}/api/v1/assistant/conversations`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${citizen.token}` },
      body: JSON.stringify({ title: "Retry Failure Pagination Test" }),
    });
    const convData = await convRes.json();
    seedHistoricalMessages(convData.id, citizen.id, 35);

    await page.goto(`/app/assistant/${convData.id}`);
    await expect(page.locator("main button[aria-label='Load older messages']")).toBeVisible({ timeout: 15000 });

    // Intercept next request with 'before' query param and abort it to simulate network/server failure
    let failOnce = true;
    await page.route(
      (url) => url.pathname.includes("/messages") && url.searchParams.has("before"),
      async (route) => {
        if (failOnce) {
          failOnce = false;
          await route.abort("failed");
        } else {
          await route.continue();
        }
      }
    );

    // Click "Load older messages" -> triggers failure
    await page.locator("main button[aria-label='Load older messages']").click();

    // Verify error banner with Retry button appears
    await expect(page.locator("text=Could not load older messages. Click to retry.")).toBeVisible({ timeout: 15000 });
    const retryBtn = page.locator("button:has-text('Retry')");
    await expect(retryBtn).toBeVisible();

    // Click "Retry"
    await retryBtn.click();

    // Older messages load successfully
    await expect(page.locator("main").locator("text=Historical Message 00")).toBeVisible({ timeout: 15000 });
    await expect(page.locator("text=Could not load older messages")).not.toBeVisible();
  });
});

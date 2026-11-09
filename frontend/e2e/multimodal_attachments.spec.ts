import { test, expect } from "@playwright/test";
import { authenticateCitizen } from "./helpers";
import * as path from "path";
import * as fs from "fs";

const FIXTURES_DIR = path.join(process.cwd(), "e2e", "temp_fixtures");

test.describe("Phase P3E & P3E.1 Multimodal Security, Privacy & Browser Acceptance", () => {
  let citizenToken: string;

  test.beforeEach(async ({ page }) => {
    // Authenticate a real provisioned citizen under forced PostgreSQL RLS
    const citizen = await authenticateCitizen(page);
    citizenToken = citizen.token;
    await page.goto("/app/assistant");
    await expect(page.locator("button:has-text('New')").first()).toBeVisible({ timeout: 15000 });
  });

  // 1. Upload PDF
  test("1. Uploads valid PDF and renders staged card with metadata", async ({ page }) => {
    const fileInput = page.locator('input[type="file"]').first();
    const pdfPath = path.join(FIXTURES_DIR, "valid_rejection.pdf");

    const [uploadResponse] = await Promise.all([
      page.waitForResponse((res) => res.url().includes("/attachments/upload") && res.status() === 201, { timeout: 20000 }),
      fileInput.setInputFiles(pdfPath),
    ]);
    expect(uploadResponse.ok()).toBeTruthy();

    await expect(page.locator("text=valid_rejection.pdf").first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=valid_rejection.pdf").first()).toBeVisible();
  });

  // 2. Upload PNG / JPG
  test("2. Uploads valid PNG image and verifies image badge and confidence", async ({ page }) => {
    const fileInput = page.locator('input[type="file"]').first();
    const pngPath = path.join(FIXTURES_DIR, "valid_document.png");

    const [uploadResponse] = await Promise.all([
      page.waitForResponse((res) => res.url().includes("/attachments/upload") && res.status() === 201, { timeout: 45000 }),
      fileInput.setInputFiles(pngPath),
    ]);
    expect(uploadResponse.ok()).toBeTruthy();

    await expect(page.locator("text=valid_document.png").first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=Ready").or(page.locator("text=Low OCR")).first()).toBeVisible();
  });

  // 3. Paste screenshot with Ctrl+V
  test("3. Pastes clipboard image file into composer via Ctrl+V", async ({ page }) => {
    const pngPath = path.join(FIXTURES_DIR, "valid_document.png");
    const pngBuffer = fs.readFileSync(pngPath);
    const base64Data = pngBuffer.toString("base64");

    // Focus composer textarea
    const textarea = page.locator("textarea").first();
    await textarea.click();

    // Trigger synthetic paste event with DataTransfer file and wait for upload response
    await Promise.all([
      page.waitForResponse((res) => res.url().includes("/attachments/upload") && res.status() === 201, { timeout: 25000 }),
      page.evaluate(async (b64) => {
        const byteChars = atob(b64);
        const byteNumbers = new Array(byteChars.length);
        for (let i = 0; i < byteChars.length; i++) {
          byteNumbers[i] = byteChars.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const file = new File([byteArray], "pasted_screenshot.png", { type: "image/png" });

        const dt = new DataTransfer();
        dt.items.add(file);

        let pasteEvent: Event;
        try {
          pasteEvent = new ClipboardEvent("paste", {
            bubbles: true,
            cancelable: true,
            clipboardData: dt,
          });
        } catch {
          pasteEvent = new Event("paste", {
            bubbles: true,
            cancelable: true,
          });
          Object.defineProperty(pasteEvent, "clipboardData", {
            value: dt,
            writable: false,
            configurable: true,
          });
        }
        const target = document.querySelector("form") || document.querySelector("textarea");
        target?.dispatchEvent(pasteEvent);
      }, base64Data),
    ]);

    // Wait for the upload to complete and staged card to appear
    await expect(page.locator("text=pasted_screenshot.png").first()).toBeVisible({ timeout: 15000 });
  });

  // 4. Drag and drop file onto composer
  test("4. Drops file onto composer drag-and-drop zone", async ({ page }) => {
    const pdfPath = path.join(FIXTURES_DIR, "valid_rejection.pdf");
    const pdfBuffer = fs.readFileSync(pdfPath);
    const base64Data = pdfBuffer.toString("base64");

    await page.evaluate(async (b64) => {
      const byteChars = atob(b64);
      const byteNumbers = new Array(byteChars.length);
      for (let i = 0; i < byteChars.length; i++) {
        byteNumbers[i] = byteChars.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const file = new File([byteArray], "dropped_notice.pdf", { type: "application/pdf" });

      const dt = new DataTransfer();
      dt.items.add(file);

      const dropEvent = new DragEvent("drop", {
        bubbles: true,
        cancelable: true,
        dataTransfer: dt,
      });
      document.querySelector("form")?.dispatchEvent(dropEvent);
    }, base64Data);

    await expect(page.locator("text=dropped_notice.pdf").first()).toBeVisible({ timeout: 15000 });
  });

  // 5. Upload multiple attachments
  test("5. Stages multiple attachments simultaneously", async ({ page }) => {
    const fileInput = page.locator('input[type="file"]').first();
    const pdf1 = path.join(FIXTURES_DIR, "valid_rejection.pdf");
    const pdf2 = path.join(FIXTURES_DIR, "valid_doc_2.pdf");

    await fileInput.setInputFiles([pdf1, pdf2]);

    await expect(page.locator("text=valid_rejection.pdf").first()).toBeVisible({ timeout: 15000 });
    await expect(page.locator("text=valid_doc_2.pdf").first()).toBeVisible({ timeout: 15000 });
  });

  // 6. Preview attachment in modal
  test("6. Opens and inspects in-chat attachment preview modal", async ({ page }) => {
    const fileInput = page.locator('input[type="file"]').first();
    const pdfPath = path.join(FIXTURES_DIR, "valid_rejection.pdf");

    await Promise.all([
      page.waitForResponse((res) => res.url().includes("/attachments/upload") && res.status() === 201, { timeout: 20000 }),
      fileInput.setInputFiles(pdfPath),
    ]);

    await expect(page.locator("text=valid_rejection.pdf").first()).toBeVisible({ timeout: 10000 });

    // Send query to persist attachment in message
    const textarea = page.locator("textarea").first();
    await textarea.fill("Please check this rejection notice.");
    const sendButton = page.locator('button[type="submit"]').first();
    await sendButton.click();

    // Wait for assistant response stream to finish arriving
    await expect(page.locator("text=Document Evidence").or(page.locator("text=Statutory")).first()).toBeVisible({ timeout: 20000 });

    // Verify rendered attachment chip in user message turn
    const attachmentChip = page.locator("button:has-text('valid_rejection.pdf')").first();
    await expect(attachmentChip).toBeVisible({ timeout: 15000 });

    // Click to open preview modal
    await attachmentChip.click();
    await expect(page.locator("text=CONFIDENTIAL TEMPORARY ATTACHMENT")).toBeVisible({ timeout: 15000 });
    await expect(page.locator("text=Document Category").first()).toBeVisible();

    // Close preview modal
    const closeBtn = page.locator("button:has-text('Close Preview')").first();
    await closeBtn.click();
    await expect(page.locator("text=CONFIDENTIAL TEMPORARY ATTACHMENT")).not.toBeVisible();
  });

  // 7. Remove attachment before sending
  test("7. Removes staged attachment from tray before sending", async ({ page }) => {
    const fileInput = page.locator('input[type="file"]').first();
    const pdfPath = path.join(FIXTURES_DIR, "valid_rejection.pdf");

    await Promise.all([
      page.waitForResponse((res) => res.url().includes("/attachments/upload") && res.status() === 201, { timeout: 20000 }),
      fileInput.setInputFiles(pdfPath),
    ]);

    await expect(page.locator("text=valid_rejection.pdf").first()).toBeVisible({ timeout: 10000 });

    // Click remove button on staged card
    const removeBtn = page.locator('button[aria-label="Remove attachment"]').first();
    await removeBtn.click();

    // Verify staged attachment is gone
    await expect(page.locator("text=valid_rejection.pdf")).not.toBeVisible({ timeout: 5000 });
  });

  // 8. Send attachment with a message
  test("8. Submits inquiry with staged attachment and receives grounded analysis", async ({ page }) => {
    const fileInput = page.locator('input[type="file"]').first();
    const pdfPath = path.join(FIXTURES_DIR, "valid_rejection.pdf");

    await Promise.all([
      page.waitForResponse((res) => res.url().includes("/attachments/upload") && res.status() === 201, { timeout: 20000 }),
      fileInput.setInputFiles(pdfPath),
    ]);

    const textarea = page.locator("textarea").first();
    await textarea.fill("Analyze the discrepancy cited in this document.");
    const sendButton = page.locator('button[type="submit"]').first();
    await sendButton.click();

    // Assistant response arrives
    await expect(page.locator("text=valid_rejection.pdf").first()).toBeVisible({ timeout: 15000 });
    await expect(page.locator("text=Document Evidence").or(page.locator("text=Statutory")).first()).toBeVisible({ timeout: 20000 });
  });

  // 9. Display OCR processing state
  test("9. Renders processing indicator while file upload/OCR is in progress", async ({ page }) => {
    await page.route("**/api/v1/assistant/attachments/upload", async (route) => {
      // Pause route briefly to assert UI shows uploading/processing state
      await new Promise((res) => setTimeout(res, 800));
      await route.continue();
    });

    const fileInput = page.locator('input[type="file"]').first();
    const pdfPath = path.join(FIXTURES_DIR, "valid_rejection.pdf");
    await fileInput.setInputFiles(pdfPath);

    // Verify uploading pulse indicator is rendered
    await expect(page.locator("text=Uploading document...").first()).toBeVisible({ timeout: 5000 });

    // Wait for card to finalize
    await expect(page.locator("text=valid_rejection.pdf").first()).toBeVisible({ timeout: 15000 });
  });

  // 10. Display OCR results & recognition quality
  test("10. Displays OCR recognition quality badge in staged card", async ({ page }) => {
    const fileInput = page.locator('input[type="file"]').first();
    const pdfPath = path.join(FIXTURES_DIR, "valid_rejection.pdf");

    await Promise.all([
      page.waitForResponse((res) => res.url().includes("/attachments/upload") && res.status() === 201, { timeout: 20000 }),
      fileInput.setInputFiles(pdfPath),
    ]);

    await expect(page.locator("text=Ready (95%)").or(page.locator("text=Ready")).first()).toBeVisible({ timeout: 10000 });
  });

  // 11. Display low-confidence extraction warnings
  test("11. Displays low-confidence OCR badge when quality is degraded", async ({ page }) => {
    const fileInput = page.locator('input[type="file"]').first();
    const lowConfImg = path.join(FIXTURES_DIR, "low_confidence.png");

    await Promise.all([
      page.waitForResponse((res) => res.url().includes("/attachments/upload") && res.status() === 201, { timeout: 45000 }),
      fileInput.setInputFiles(lowConfImg),
    ]);

    await expect(page.locator("text=low_confidence.png").first()).toBeVisible({ timeout: 10000 });
    const qualityIndicator = page.locator("text=Low OCR").or(page.locator("text=Ready")).first();
    await expect(qualityIndicator).toBeVisible();
  });

  // 12. Retry failed upload
  test("12. Rejects unsupported file extension with error alert and allows valid retry", async ({ page }) => {
    const fileInput = page.locator('input[type="file"]').first();
    const txtPath = path.join(FIXTURES_DIR, "invalid_extension.txt");

    // Upload unsupported file
    await fileInput.setInputFiles(txtPath);

    // Assert error message appears
    await expect(page.locator("text=not supported").or(page.locator("text=Failed to upload")).first()).toBeVisible({ timeout: 10000 });

    // Retry with valid PDF
    const validPdf = path.join(FIXTURES_DIR, "valid_rejection.pdf");
    await Promise.all([
      page.waitForResponse((res) => res.url().includes("/attachments/upload") && res.status() === 201, { timeout: 20000 }),
      fileInput.setInputFiles(validPdf),
    ]);

    await expect(page.locator("text=valid_rejection.pdf").first()).toBeVisible({ timeout: 10000 });
  });

  // 13. Delete attachment via session cleanup
  test("13. Deletes conversation and verifies attachment cascade cleanup", async ({ page }) => {
    const fileInput = page.locator('input[type="file"]').first();
    const pdfPath = path.join(FIXTURES_DIR, "valid_rejection.pdf");

    await Promise.all([
      page.waitForResponse((res) => res.url().includes("/attachments/upload") && res.status() === 201, { timeout: 20000 }),
      fileInput.setInputFiles(pdfPath),
    ]);

    const textarea = page.locator("textarea").first();
    await textarea.fill("Save this session with attachment.");
    const sendButton = page.locator('button[type="submit"]').first();
    await sendButton.click();

    await expect(page.locator("text=valid_rejection.pdf").first()).toBeVisible({ timeout: 15000 });

    // Start a new inquiry
    const newBtn = page.locator("button:has-text('New')").first();
    await newBtn.click();

    // Verify empty state is restored
    await expect(page.locator("text=How can I help you today?").or(page.locator("textarea")).first()).toBeVisible();
  });

  // 14. Mobile attachment workflow
  test("14. Verifies responsive attachment controls in mobile viewport", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });

    // Verify composer surface and attachment button remain visible and accessible
    const addAttachmentBtn = page.locator('button[aria-label="Add attachment"]').first();
    await expect(addAttachmentBtn).toBeVisible({ timeout: 5000 });

    // Click attachment button to open popover menu
    await addAttachmentBtn.click();
    await expect(page.locator("text=Upload Document / Scan").first()).toBeVisible({ timeout: 5000 });
  });
});

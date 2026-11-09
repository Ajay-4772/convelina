import { Page } from "@playwright/test";

export interface TestCitizen {
  id: string;
  firebase_uid: string;
  email: string;
  full_name: string;
  token: string;
}

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Provisions a real citizen in the PostgreSQL database via FastAPI under forced RLS.
 */
export async function provisionTestCitizenApi(
  options?: { uid?: string; email?: string; fullName?: string }
): Promise<TestCitizen> {
  const uid = options?.uid || `cit_e2e_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
  const email = options?.email || `${uid}@example.com`;
  const fullName = options?.fullName || "Aarav Sharma";
  const token = `test_token_:${uid}:${email}:${fullName}`;

  const res = await fetch(`${API_URL}/api/v1/auth/provision`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      email,
      full_name: fullName,
      phone_number: "+919876543210",
      date_of_birth: "1992-08-15",
      address: "24, Gandhi Nagar, Bengaluru, Karnataka - 560001",
      father_name: "Ramesh Sharma",
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(`Failed to provision test citizen: HTTP ${res.status} - ${JSON.stringify(err)}`);
  }

  const profile = await res.json();
  return {
    id: profile.id,
    firebase_uid: uid,
    email,
    full_name: fullName,
    token,
  };
}

/**
 * Provisions a real citizen in the PostgreSQL database via FastAPI under forced RLS,
 * and sets the active session in browser localStorage.
 */
export async function authenticateCitizen(
  page: Page,
  options?: { uid?: string; email?: string; fullName?: string }
): Promise<TestCitizen> {
  const citizen = await provisionTestCitizenApi(options);

  // 1. Register init script so every navigation automatically has the token in localStorage
  await page.addInitScript((tok) => {
    try {
      localStorage.setItem("convelina_test_token", tok);
    } catch {}
  }, citizen.token);

  // 2. Set token in browser localStorage immediately on active page
  await page.goto("/");
  await page.evaluate((tok) => {
    try {
      localStorage.setItem("convelina_test_token", tok);
    } catch {}
  }, citizen.token);

  return citizen;
}

/**
 * Creates a synthetic minimal PDF buffer with specific text for OCR testing.
 */
export function generateSyntheticPdfBuffer(textLines: string[]): Buffer {
  const content = textLines.join("\n");
  const streamData = `BT /F1 12 Tf 50 700 Td (${content}) Tj ET`;
  const streamLen = streamData.length;

  const pdf = `%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj
4 0 obj << /Length ${streamLen} >> stream
${streamData}
endstream
endobj
5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 
0000000336 00000 n 
trailer << /Size 6 /Root 1 0 R >>
startxref
413
%%EOF`;
  return Buffer.from(pdf, "utf-8");
}

/**
 * Creates a valid synthetic 1x1 PNG image buffer for testing.
 */
export function generateSyntheticPngBuffer(): Buffer {
  return Buffer.from(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
    "base64"
  );
}

/**
 * Programmatically uploads a synthetic document via the FastAPI backend under forced RLS.
 */
export async function uploadDocumentApi(
  token: string,
  docType: string,
  lines: string[]
): Promise<any> {
  const pdfBuffer = generateSyntheticPdfBuffer(lines);
  const formData = new FormData();
  formData.append("document_type", docType);
  const blob = new Blob([new Uint8Array(pdfBuffer)], { type: "application/pdf" });
  formData.append("file", blob, `synthetic_${docType}.pdf`);

  const res = await fetch(`${API_URL}/api/v1/documents/upload`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(`Upload failed HTTP ${res.status}: ${JSON.stringify(err)}`);
  }
  return await res.json();
}

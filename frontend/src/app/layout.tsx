import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "../context/AuthContext";

export const metadata: Metadata = {
  title: "CONVELINA — Your documents, made easier.",
  description:
    "CONVELINA detects clerical mismatches across Indian identity records (Aadhaar, PAN, Passport, Class 10/12, and EPF) — providing source-grounded statutory guidance, authentic forms, and cryptographic verification.",
  applicationName: "CONVELINA",
  authors: [{ name: "CONVELINA" }],
  keywords: [
    "CONVELINA",
    "document reconciliation",
    "identity verification",
    "Aadhaar conflict detection",
    "PAN correction",
    "EPFO UAN mismatch",
    "passport verification",
    "statutory guidance",
    "Ed25519 PKI",
  ],
  openGraph: {
    title: "CONVELINA — Your documents, made easier.",
    description:
      "Understand document differences, find the right forms, and get clear guidance on what to do next.",
    siteName: "CONVELINA",
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "CONVELINA — Your documents, made easier.",
    description:
      "Understand document differences, find the right forms, and get clear guidance on what to do next.",
  },
  icons: {
    icon: "/favicon.png",
    shortcut: "/favicon.png",
    apple: "/logo.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased selection:bg-[#111111] selection:text-white">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}

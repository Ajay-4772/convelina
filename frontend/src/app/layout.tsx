import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Consolith | AI Identity Conflict Detection & Government Correction Assistance",
  description: "Detect identity document conflicts and access RAG-grounded correction guidance for Indian citizens.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased selection:bg-blue-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}

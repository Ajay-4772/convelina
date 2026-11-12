"use client";

import React from "react";
import { ExternalLink } from "lucide-react";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

/**
 * Safe, robust Markdown renderer for statutory assistant answers.
 * Parses headers, bold, italics, inline code, code blocks, lists, blockquotes, tables, and links.
 * Zero external library dependencies; fully XSS-safe via React DOM node generation.
 */
export default function MarkdownRenderer({ content, className = "" }: MarkdownRendererProps) {
  if (!content) return null;

  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];

  let i = 0;
  let keyIndex = 0;

  while (i < lines.length) {
    const line = lines[i];

    // 1. Code blocks (```lang ... ```)
    if (line.trim().startsWith("```")) {
      const codeLines: string[] = [];
      const lang = line.trim().slice(3).trim();
      i++;
      while (i < lines.length && !lines[i].trim().startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      i++; // skip closing ```
      elements.push(
        <div key={`code-${keyIndex++}`} className="my-3 rounded-md bg-[#1F1E1D] text-[#FAF9F5] p-3 text-xs font-mono overflow-x-auto">
          {lang && (
            <div className="text-[10px] text-[#A0A09B] uppercase font-sans mb-1 pb-1 border-b border-white/10 tracking-wider">
              {lang}
            </div>
          )}
          <pre className="leading-relaxed whitespace-pre">{codeLines.join("\n")}</pre>
        </div>
      );
      continue;
    }

    // 2. Headings (###, ##, #)
    if (line.startsWith("### ")) {
      elements.push(
        <h4 key={`h4-${keyIndex++}`} className="font-serif text-sm sm:text-base font-semibold text-[#1F1E1D] mt-4 mb-1.5">
          {renderInline(line.slice(4))}
        </h4>
      );
      i++;
      continue;
    }
    if (line.startsWith("## ")) {
      elements.push(
        <h3 key={`h3-${keyIndex++}`} className="font-serif text-base sm:text-lg font-semibold text-[#1F1E1D] mt-5 mb-2">
          {renderInline(line.slice(3))}
        </h3>
      );
      i++;
      continue;
    }
    if (line.startsWith("# ")) {
      elements.push(
        <h2 key={`h2-${keyIndex++}`} className="font-serif text-lg sm:text-xl font-bold text-[#1F1E1D] mt-6 mb-2">
          {renderInline(line.slice(2))}
        </h2>
      );
      i++;
      continue;
    }

    // 3. Blockquotes (> ...)
    if (line.startsWith("> ")) {
      const quoteLines: string[] = [line.slice(2)];
      i++;
      while (i < lines.length && lines[i].startsWith("> ")) {
        quoteLines.push(lines[i].slice(2));
        i++;
      }
      elements.push(
        <blockquote
          key={`quote-${keyIndex++}`}
          className="my-3 pl-3.5 border-l-2 border-[#C96442] bg-[#FAF9F5] py-2 pr-3 rounded-r text-xs sm:text-sm text-[#4A4946] italic leading-relaxed"
        >
          {quoteLines.map((ql, qidx) => (
            <p key={qidx} className={qidx > 0 ? "mt-1" : ""}>
              {renderInline(ql)}
            </p>
          ))}
        </blockquote>
      );
      continue;
    }

    // 4. Tables (| col | col |)
    if (line.trim().startsWith("|") && line.trim().endsWith("|")) {
      const tableLines: string[] = [line.trim()];
      i++;
      while (i < lines.length && lines[i].trim().startsWith("|") && lines[i].trim().endsWith("|")) {
        tableLines.push(lines[i].trim());
        i++;
      }

      if (tableLines.length >= 2) {
        const headerRow = parseTableRow(tableLines[0]);
        // line 1 is usually divider |---|---|
        const dataRows = tableLines.slice(2).map(parseTableRow);

        elements.push(
          <div key={`table-${keyIndex++}`} className="my-3 overflow-x-auto rounded border border-[#E5E5E0]">
            <table className="w-full text-left text-xs border-collapse font-sans">
              <thead className="bg-[#FAF9F5] border-b border-[#E5E5E0] text-[#1F1E1D]">
                <tr>
                  {headerRow.map((cell, cidx) => (
                    <th key={cidx} className="px-3 py-2 font-semibold">
                      {renderInline(cell)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E5E5E0] bg-white">
                {dataRows.map((row, ridx) => (
                  <tr key={ridx} className="hover:bg-[#FAF9F5]/60 transition-colors">
                    {row.map((cell, cidx) => (
                      <td key={cidx} className="px-3 py-2 text-[#4A4946]">
                        {renderInline(cell)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
        continue;
      }
    }

    // 5. Unordered list (* item, - item)
    if (line.trim().startsWith("- ") || line.trim().startsWith("* ")) {
      const listItems: string[] = [line.trim().slice(2)];
      i++;
      while (i < lines.length && (lines[i].trim().startsWith("- ") || lines[i].trim().startsWith("* "))) {
        listItems.push(lines[i].trim().slice(2));
        i++;
      }
      elements.push(
        <ul key={`ul-${keyIndex++}`} className="my-2.5 space-y-1.5 pl-5 list-disc text-xs sm:text-sm text-[#1F1E1D] leading-relaxed">
          {listItems.map((item, idx) => (
            <li key={idx} className="pl-1">
              {renderInline(item)}
            </li>
          ))}
        </ul>
      );
      continue;
    }

    // 6. Numbered list (1. item, 2. item)
    if (/^\d+\.\s/.test(line.trim())) {
      const listItems: string[] = [line.trim().replace(/^\d+\.\s/, "")];
      i++;
      while (i < lines.length && /^\d+\.\s/.test(lines[i].trim())) {
        listItems.push(lines[i].trim().replace(/^\d+\.\s/, ""));
        i++;
      }
      elements.push(
        <ol key={`ol-${keyIndex++}`} className="my-2.5 space-y-1.5 pl-5 list-decimal text-xs sm:text-sm text-[#1F1E1D] leading-relaxed">
          {listItems.map((item, idx) => (
            <li key={idx} className="pl-1">
              {renderInline(item)}
            </li>
          ))}
        </ol>
      );
      continue;
    }

    // 7. Empty lines / Paragraph breaks
    if (line.trim() === "") {
      i++;
      continue;
    }

    // 8. Normal Paragraph
    elements.push(
      <p key={`p-${keyIndex++}`} className="my-2 text-xs sm:text-sm text-[#1F1E1D] leading-relaxed">
        {renderInline(line)}
      </p>
    );
    i++;
  }

  return <div className={`prose-convelina space-y-1 ${className}`}>{elements}</div>;
}

/** Parses pipe-delimited table rows */
function parseTableRow(line: string): string[] {
  const inner = line.trim().replace(/^\|/, "").replace(/\|$/, "");
  return inner.split("|").map((c) => c.trim());
}

/**
 * Parses inline markdown: **bold**, *italic*, `code`, and [link](url)
 */
function renderInline(text: string): React.ReactNode {
  if (!text) return "";

  // Split by inline tokens: links, code, bold, italic
  const parts: React.ReactNode[] = [];
  // Regex to match [text](url), `code`, **bold**, *italic*
  const tokenRegex = /(\[[^\]]+\]\([^)]+\)|`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)/g;
  const segments = text.split(tokenRegex);

  for (let j = 0; j < segments.length; j++) {
    const seg = segments[j];
    if (!seg) continue;

    // Link: [text](url)
    if (seg.startsWith("[") && seg.includes("](") && seg.endsWith(")")) {
      const match = seg.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
      if (match) {
        const linkText = match[1];
        const linkUrl = match[2].trim();
        const isSafeHref = (url: string): boolean => {
          if (!url) return false;
          if (url.startsWith("/") && !url.startsWith("//")) return true;
          try {
            const parsed = new URL(url);
            return parsed.protocol === "https:" || parsed.protocol === "http:" || parsed.protocol === "mailto:";
          } catch {
            return false;
          }
        };

        if (!isSafeHref(linkUrl)) {
          parts.push(
            <span key={`l-blocked-${j}`} className="font-medium text-neutral-700" title="Blocked unsafe link protocol">
              {linkText}
            </span>
          );
          continue;
        }

        parts.push(
          <a
            key={`l-${j}`}
            href={linkUrl}
            target="_blank"
            rel="noopener noreferrer nofollow"
            className="inline-flex items-center gap-0.5 text-[#0066CC] hover:underline font-medium"
          >
            <span>{linkText}</span>
            <ExternalLink className="w-2.5 h-2.5 inline-block ml-0.5 opacity-70" />
          </a>
        );
        continue;
      }
    }

    // Code: `code`
    if (seg.startsWith("`") && seg.endsWith("`") && seg.length > 1) {
      parts.push(
        <code
          key={`c-${j}`}
          className="px-1.5 py-0.5 rounded bg-[#EFEEEA] text-[#1F1E1D] font-mono text-[11px] sm:text-xs"
        >
          {seg.slice(1, -1)}
        </code>
      );
      continue;
    }

    // Bold: **text**
    if (seg.startsWith("**") && seg.endsWith("**") && seg.length > 4) {
      parts.push(
        <strong key={`b-${j}`} className="font-semibold text-[#1F1E1D]">
          {seg.slice(2, -2)}
        </strong>
      );
      continue;
    }

    // Italic: *text*
    if (seg.startsWith("*") && seg.endsWith("*") && seg.length > 2) {
      parts.push(
        <em key={`i-${j}`} className="italic text-[#4A4946]">
          {seg.slice(1, -1)}
        </em>
      );
      continue;
    }

    // Plain text
    parts.push(seg);
  }

  return <>{parts}</>;
}


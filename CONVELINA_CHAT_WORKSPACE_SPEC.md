# CONVELINA — Conversational AI Workspace Design Specification
## Claude-Inspired Minimalist Interface • Contextual Discrepancy Grounding • In-Chat Artifact Downloads

**Document Version:** 3.1.0 (Phase P3B Implementation Verified)  
**Design Reference:** Visual patterns from Claude 3.5 / 3.7 web interface  
**Aesthetic Baseline:** Editorial white/light mode, warm stone neutral (`#FAF9F5`), crisp hairline dividers (`#E5E5E0`), high-contrast ink slate (`#1F1E1D`), terracotta asterisk brand mark (`#C96442`), zero neon clutter  
**Implementation Status:** Phase P3B Implemented & Verified (AssistantWorkspace, AssistantSidebar, AssistantComposer, ConversationSearchModal, MarkdownRenderer)  

---

## 1. Visual & Interactive Design Principles

The CONVELINA conversational interface is designed to evoke calm, clarity, and authority when citizens face stressful bureaucratic identity conflicts. It directly adapts the clean, content-first patterns of the supplied reference screenshots:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ [☰] [⟨ ⟩]                                                     [Citizen] [User Avatar] │
├──────────────────────────┬─────────────────────────────────────────────────────────────┤
│ COLLAPSIBLE SIDEBAR      │ MAIN CHAT CANVAS                                            │
│                          │                                                             │
│  [+ New Inquiry  Ctrl+N] │                                                             │
│  🔍 Search past inquiries│                     ✳️ Good afternoon, Ajay                 │
│                          │                                                             │
│  📁 Document Repository  │         "I can help resolve your Aadhaar, PAN, Passport,    │
│  ⚖️ Discrepancies (2)    │          or EPFO mismatches with verified official forms."  │
│                          │                                                             │
│  PINNED                  │                                                             │
│  📌 Passport DOB Mismatch│                                                             │
│  📌 EPFO Joint Correction│                                                             │
│                          │        ┌──────────────────────────────────────────────────┐ │
│  CHATS                   │        │ [+] How can I help you resolve a discrepancy?    │ │
│  • Aadhaar Name Spelling │        │                                                  │ │
│  • Gazette Parentage Sync│        │ [Gemini 2.5 Flash • RAG]   [🌐 EN ▾]  [🎙️]  [⏎]   │ │
│  • Form 49A Checklist    │        └──────────────────────────────────────────────────┘ │
│                          │                                                             │
│  [⚙️ Profile & Settings] │                                                             │
└──────────────────────────┴─────────────────────────────────────────────────────────────┘
```

1. **Light & Editorial Palette**:
   * Canvas Background: `#FAF9F6` (Warm Off-White / Alabaster).
   * Surface & Cards: `#FFFFFF` (Pure Crisp White) with `border border-[#E7E5E0]`.
   * Primary Text: `#111111` (Deep High-Contrast Ink).
   * Secondary Text: `#5E5E5E` (Warm Medium Gray).
   * Subtle Borders: `#E7E5E0` (Hairline Stone Gray).
   * Accents: Deep Charcoal (`#1F1F1F`), Success Green (`#0D652D`), Warning Amber (`#B06000`), Discrepancy Crimson (`#BA1A1A`).
2. **Whitespace & Typography**:
   * Header Typography: Crisp serif or humanist editorial font (Georgia / Inter / Playfair).
   * Body Typography: High-legibility sans-serif (`Inter`, `system-ui`) with generous line-height (`leading-relaxed`).
3. **Restraint & Elimination of Noise**:
   * Zero garish gradients, zero floating neon blobs, zero animated decorative cards.
   * Visual weight is allocated strictly to **verified evidence, statutory warnings, and actionable download buttons**.

---

## 2. Layout & Component Architecture

### 2.1 Collapsible Left Navigation Sidebar (`w-72` Desktop, Responsive Drawer Mobile)
* **Top Header & Toggle**:
  * Collapsible hamburger button (`☰`) with tooltip.
  * Brand emblem (`CONVELINA`) in subtle serif lettering.
* **Primary Action**:
  * `+ New Inquiry` button with keyboard shortcut badge `Ctrl+N` (or `⌘N` on macOS).
  * Clears active conversation ID, resets input buffer, and navigates to clean welcome canvas.
* **Fast In-Memory Search**:
  * Compact search bar with magnifying glass icon.
  * Instant client-side filtering across conversation titles and message snippets.
* **Persistent Navigation Links**:
  * `📁 Document Repository` (`/app/forms`): Quick access to the statutory catalog.
  * `⚖️ Discrepancies` (`/app/inconsistencies`): Quick access to multi-document comparisons.
* **Pinned Inquiries Section**:
  * Pinned conversation items with small pin icon (`📌`).
  * Right-click / hover context menu to unpin.
* **Chronological Conversation List**:
  * Grouped by relative recency: *Today*, *Yesterday*, *Previous 7 Days*, *Older*.
  * Truncated single-line titles with hover actions:
    * Pin (`📌`)
    * Rename (`✏️`)
    * Delete (`🗑️`) with confirmation modal.
* **Footer Profile Card**:
  * User avatar, citizen name, email, and link to `/app/profile`.

---

### 2.2 Main Conversation Canvas
* **Empty / Welcome State**:
  * Displayed when `messages.length === 0`.
  * Centered warm greeting: `"Good morning / afternoon / evening, [Full Name]"`.
  * Brand starburst icon or statutory emblem.
  * 3 quick-start prompt pills:
    * `"What documents prove date of birth in Passport?"`
    * `"How do I submit an EPFO Joint Declaration form?"`
    * `"Can you draft a name correction letter to UIDAI?"`
* **Message Thread (`flex-1 overflow-y-auto`)**:
  * User message bubble: Clean right-aligned or left-padded bubble with `#F4F3EF` background, `#111111` text, crisp border.
  * Assistant message bubble: Left-aligned, full-width reader layout with generous line-height, rendered Markdown, bold headings, ordered lists, and interactive artifact cards.
  * Auto-scroll behavior: Smooth scroll to bottom on new message submission and token generation.

---

## 3. The Floating Message Composer Specification

The floating composer adapts the exact pill layout from Reference Screenshot 2 (`media_1793795202625_d1c5e2ef.png`):

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  [+]  | Write a message or paste a document screenshot...          [🎙️]  [🌐 EN ▾] [↑] │
│                                                                                        │
│  [⚡ AI Grounded (Gemini 2.5 Flash)]  •  [📎 aadhaar_scan.pdf (1.2MB) ✖]               │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Input Capabilities & Triggers
* **Auto-Expanding Textarea**: Single-line starting height (44px), expanding smoothly up to 5 lines (140px) before activating vertical scroll.
* **Plus (`+`) Attachment Action**:
  * Clicking opens native file selection dialog.
  * Supported MIME types: `application/pdf`, `image/png`, `image/jpeg`.
  * Maximum size: 10 MB per file.
  * Staged attachment chips appear above the input bar with file name, size, and remove (`✖`) action.
* **Clipboard Image Paste (`Ctrl+V` / `⌘V`)**:
  * Dedicated event listener on window and input container.
  * When clipboard data contains `items[i].type.startsWith("image/")`:
    * Converts blob to temporary object URL for preview chip.
    * Encodes file for secure multipart upload.
    * No user manual save required.
* **Language Selector Dropdown (`🌐 Language`)**:
  * Supported options: English (`EN`), Tamil (`தமிழ்`), Hindi (`हिन्दी`), Telugu (`తెలుగు`), Kannada (`ಕನ್ನಡ`), Malayalam (`മലയാളം`), Bengali (`বাংলা`), Marathi (`मराठी`).
  * Passes `language` parameter to backend chat request.
  * LLM responds in chosen language while maintaining exact official form IDs and URLs in English.
* **Live Provider Mode Indicator**:
  * `[⚡ AI Grounded (Gemini 2.5 Flash)]`: Real-time AI generation grounded in verified RAG chunks.
  * `[🛡️ Offline Statutory Mode]`: Deterministic resolution mapping fallback active.
  * `[⚠️ Insufficient Evidence]`: Query falls below 0.55 relevance floor.
  * **Never displays fake or misleading model options.**
* **Dictation / Microphone Action (`🎙️`)**:
  * Uses Web Speech API (`webkitSpeechRecognition`) where supported by modern browsers.
  * Click to toggle listening state with pulsing red indicator.

---

## 4. Interactive In-Chat Message Artifacts

### 4.1 In-Chat Official Form Download Card
Rendered when the assistant mentions or suggests an official statutory form:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 📄 UIDAI Standard Certificate Form (Annexure I)                                        │
│ Issuing Authority: Unique Identification Authority of India (UIDAI)                    │
│ Category: Aadhaar • Version: 2023.1 • Verification: VERIFIED                           │
│                                                                                        │
│ Purpose: Standard certificate issued by Gazetted Officer/Tehsildar for address or      │
│          name update in the absence of primary POI/POA documents.                      │
│                                                                                        │
│ [📥 Download Official PDF]     [👁️ View Field Instructions]     [🔗 Official Portal]   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

* **Download Trigger**: Calls authorized backend streaming endpoint `/api/v1/knowledge/forms/{id}/download`.
* **Field Instructions**: Expands an inline collapsible guide explaining what details must be filled in each field.

---

### 4.2 Legal Representation & Letter Draft Card
Rendered when the assistant drafts a formal representation or petition:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 📝 Formal Representation: Name Discrepancy Correction                                  │
│ Recipient: Regional Passport Officer, Chennai                                          │
│ Statutory Reference: Passports Act, 1967 • Chapter 8 Name Correction Guidelines        │
│                                                                                        │
│ To,                                                                                    │
│ The Regional Passport Officer,                                                         │
│ Regional Passport Office, Rayala Towers, Chennai - 600002.                             │
│                                                                                        │
│ Subject: Representation for correction of spelling in Given Name (Ref: ARN 2400...)     │
│ ...                                                                                    │
│                                                                                        │
│ [📋 Copy to Clipboard]     [📄 Export DOCX]     [📑 Export PDF]     [✏️ Edit Content]   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 4.3 Mandatory Statutory Disclaimer Callout
Every assistant turn terminates with a standardized statutory footer:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ ⚖️ AUTOMATED COMPARISON RESULT • NOT OFFICIAL GOVERNMENT VERIFICATION                  │
│ This guidance is synthesized from verified public circulars and deterministic record   │
│ comparison. It does not constitute legal counsel or official government verification.   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Responsive Behavior & Accessibility

* **Breakpoints**:
  * Desktop ($\ge 1024\text{px}$): Dual pane with fixed sidebar and centered 800px chat canvas.
  * Tablet ($768\text{px} - 1023\text{px}$): Sidebar collapses into slide-over backdrop drawer.
  * Mobile ($< 768\text{px}$): Full-width canvas with sticky bottom composer and header drawer toggle.
* **Keyboard Navigation**:
  * `Ctrl+N` / `⌘N`: New Inquiry.
  * `Enter`: Submit inquiry (when not pressing Shift).
  * `Shift+Enter`: Insert newline in textarea.
  * `Escape`: Close modals, dropdowns, and mobile drawers.
  * Accessible focus rings (`focus:ring-2 focus:ring-[#111111] focus:outline-none`).


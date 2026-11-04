# Consolith Product Demonstration Video — Google Veo Storyboard & Prompt Specification

## Overview
This document specifies the exact visual sequence, timing, voiceover narrative, and prompt structure for generating a high-definition product demonstration video for Consolith using Google Veo or screen recording capture tools.

---

## 1. Video Specifications
- **Target Resolution:** 1920x1080 (1080p, 60fps) or 4K UHD (3840x2160)
- **Target Duration:** 90 seconds (1 minute 30 seconds)
- **Aspect Ratio:** 16:9 widescreen
- **Tone & Aesthetic:** Minimalist, calm, trustworthy, warm off-white tones (`#faf9f6`), charcoal typography (`#18181b`), subtle motion graphics, clean UI zooms.
- **Strict Requirement:** Must demonstrate the actual Consolith application screens and workflow. No fake interfaces, no exaggerated claims, no invented government affiliations.

---

## 2. Sequence & Storyboard Breakdown

### Scene 1: The Problem & Opening (0:00 - 0:15)
- **Visuals:** Subtle macro zoom into an Indian resident's desk showing an Aadhaar Card and PAN Card. The camera smoothly glides to a sleek laptop screen displaying the Consolith homepage (`https://consolith.gov.guide`).
- **On-Screen Text:** "Your documents, understood."
- **Voiceover / Caption:** "For millions of Indian citizens, small spelling differences or abbreviated initials across official identity records can delay passport applications, bank KYC, or job onboarding."

### Scene 2: Secure Citizen Login & Upload (0:15 - 0:30)
- **Visuals:** The user enters the private citizen workspace (`/app`). A clean drag-and-drop zone appears. The user drops two sample documents: an Aadhaar card image and a PAN card image.
- **Key Detail:** The interface shows automatic Aadhaar number masking (`XXXX-XXXX-4819`) and a progress indicator showing ephemeral OCR processing.
- **Voiceover / Caption:** "With Consolith, simply upload your documents. Your files are processed securely in temporary memory with immediate identity number masking."

### Scene 3: Discrepancy Detection in Action (0:30 - 0:50)
- **Visuals:** The comparison view highlights the discrepancy between "Ramanathan Kumar" on Aadhaar and "K. Ramanathan" on PAN card. An amber indicator clearly explains: "Initial expansion detected with matching Date of Birth (14/08/1988)."
- **Voiceover / Caption:** "Consolith instantly cross-examines demographic fields, identifying clerical differences without labeling normal variations as fraud."

### Scene 4: AI Resolution Guidance (0:50 - 1:10)
- **Visuals:** The user clicks "Ask Guidance". The AI assistant provides a concise, step-by-step procedure: "Submit PAN Form 49A to expand your initial, using Aadhaar as Proof of Identity."
- **Key Detail:** The response cites the verified Income Tax Department PAN Rectification Guidelines.
- **Voiceover / Caption:** "Get clear, actionable guidance grounded strictly in verified statutory regulations from UIDAI, Income Tax, MEA, and EPFO."

### Scene 5: Official Forms & Pre-filled Drafts (1:10 - 1:25)
- **Visuals:** The user browses official application forms, downloads Form 49A, and generates a pre-filled Name Correction Affidavit in PDF format.
- **Voiceover / Caption:** "Access authentic government forms directly, download pre-filled draft letters, and take the ambiguity out of your next administrative step."

### Scene 6: Closing & Call to Action (1:25 - 1:30)
- **Visuals:** Camera pulls back to reveal the clean, responsive Consolith interface. A sleek closing card displays the Consolith emblem, URL (`https://consolith.gov.guide`), and support contact (`consolithofficial@gmail.com`).
- **Voiceover / Caption:** "Consolith. Make your next document-related step clearer. Get started today."

---

## 3. Google Veo Prompt Templates

### Prompt 1 (Establishing Shot & Hero UI):
```text
Cinematic high-angle studio shot of a modern, minimalist web application titled "Consolith" displayed on a premium laptop screen. Warm off-white background (#faf9f6), dark charcoal serif headings, sleek white card surfaces with subtle borders. Smooth natural camera push-in towards the headline "Your documents, understood." Photorealistic lighting, 4k resolution, clean modern product aesthetic.
```

### Prompt 2 (Document Analysis & Discrepancy UI):
```text
Close-up smooth screen capture showing an identity document comparison tool. Left card displays "Aadhaar Card" with masked number XXXX-XXXX-4819 and name "Ramanathan Kumar". Right card displays "PAN Card" with name highlighted in soft amber "K. Ramanathan". Elegant scanning highlight line passes across the cards, revealing an analysis badge "Initial Expansion Detected". No noise, ultra-clean UI, smooth 60fps motion graphics.
```

### Prompt 3 (AI Guidance & Resolution):
```text
Sleek SaaS interface showing an AI assistant dialogue box with Google Gemini grounded response. A question asks "How do I resolve name mismatch between Aadhaar and PAN?", followed by a clean response card citing "Income Tax PAN Rectification Guidelines". Crisp typography, smooth fade-in animation, professional software demonstration style.
```

---

## 4. Integration Details
- The landing page video player at [frontend/src/components/landing/ProductDemo.tsx](file:///c:/Users/ajaya/Desktop/consolin/frontend/src/components/landing/ProductDemo.tsx) is equipped with full video controls (play, pause, seek bar, time duration, volume, chapter selection, and subtitle captions).
- When a rendered `.mp4` or `.webm` asset is exported, place it in `frontend/public/assets/product_demo.mp4` and attach the `<video>` element to the player container.

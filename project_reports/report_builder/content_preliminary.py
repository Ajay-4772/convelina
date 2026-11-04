# -*- coding: utf-8 -*-
"""
Preliminary pages generator for CONVELINA Academic Report.
Includes:
- Cover Page & Title Page
- Bonafide Certificate (Dr. Zulaikha Beevi S, Professor; Dr. Sathish Kumar S, HOD)
- Certificate of Evaluation
- Acknowledgement
- Abstract
- Table of Contents
- List of Tables
- List of Figures
- List of Abbreviations and Nomenclature
"""

import os
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

from .styles import FONT_NAME, COLOR_BLACK, COLOR_NAVY

def add_cover_page(doc, logo_path):
    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_inst.paragraph_format.space_before = Pt(0)
    p_inst.paragraph_format.space_after = Pt(2)
    p_inst.paragraph_format.line_spacing = 1.15
    r = p_inst.add_run("ANNA UNIVERSITY :: CHENNAI 600 025\n")
    r.font.name = FONT_NAME
    r.font.size = Pt(14)
    r.font.bold = True

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(12)
    r = p_sub.add_run("FORMAT FOR PREPARATION OF PROJECT REPORT FOR B.E. / B. TECH.")
    r.font.name = FONT_NAME
    r.font.size = Pt(11)
    r.font.bold = True

    if os.path.exists(logo_path):
        p_logo = doc.add_paragraph()
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo.paragraph_format.space_before = Pt(4)
        p_logo.paragraph_format.space_after = Pt(12)
        p_logo.add_run().add_picture(logo_path, width=Inches(1.5))

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(8)
    p_title.paragraph_format.space_after = Pt(14)
    p_title.paragraph_format.line_spacing = 1.3
    r_title = p_title.add_run("CONVELINA: AN AI-POWERED IDENTITY DOCUMENT CONFLICT DETECTION AND GOVERNMENT CORRECTION ASSISTANCE SYSTEM USING LLMS AND RAG")
    r_title.font.name = FONT_NAME
    r_title.font.size = Pt(16)
    r_title.font.bold = True

    p_rep = doc.add_paragraph()
    p_rep.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_rep.paragraph_format.space_before = Pt(4)
    p_rep.paragraph_format.space_after = Pt(2)
    r_rep = p_rep.add_run("A PROJECT REPORT (PHASE – I)")
    r_rep.font.name = FONT_NAME
    r_rep.font.size = Pt(14)
    r_rep.font.bold = True

    p_by = doc.add_paragraph()
    p_by.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_by.paragraph_format.space_before = Pt(2)
    p_by.paragraph_format.space_after = Pt(6)
    r_by = p_by.add_run("Submitted by")
    r_by.font.name = FONT_NAME
    r_by.font.size = Pt(14)
    r_by.font.italic = True

    p_cands = doc.add_paragraph()
    p_cands.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cands.paragraph_format.space_before = Pt(2)
    p_cands.paragraph_format.space_after = Pt(10)
    p_cands.paragraph_format.line_spacing = 1.2
    candidates = [
        ("AJAY M", "113023243003"),
        ("ADITHYA B", "113023243002"),
        ("KAMESH G", "113023243041")
    ]
    for name, reg in candidates:
        r = p_cands.add_run(f"{name} ({reg})\n")
        r.font.name = FONT_NAME
        r.font.size = Pt(14)
        r.font.bold = True

    p_deg = doc.add_paragraph()
    p_deg.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_deg.paragraph_format.space_before = Pt(4)
    p_deg.paragraph_format.space_after = Pt(4)
    p_deg.paragraph_format.line_spacing = 1.2
    r_deg = p_deg.add_run("in partial fulfillment for the award of the degree\nof\n")
    r_deg.font.name = FONT_NAME
    r_deg.font.size = Pt(13)
    r_deg.font.italic = True
    r_deg2 = p_deg.add_run("BACHELOR OF TECHNOLOGY\nin\nARTIFICIAL INTELLIGENCE AND DATA SCIENCE")
    r_deg2.font.name = FONT_NAME
    r_deg2.font.size = Pt(14)
    r_deg2.font.bold = True

    p_col = doc.add_paragraph()
    p_col.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_col.paragraph_format.space_before = Pt(10)
    p_col.paragraph_format.space_after = Pt(2)
    p_col.paragraph_format.line_spacing = 1.2
    r_col = p_col.add_run("VEL TECH HIGH TECH Dr. RANGARAJAN Dr. SAKUNTHALA ENGINEERING COLLEGE\nAn Autonomous Institution\n")
    r_col.font.name = FONT_NAME
    r_col.font.size = Pt(13)
    r_col.font.bold = True

    r_univ = p_col.add_run("ANNA UNIVERSITY : CHENNAI 600 025\n")
    r_univ.font.name = FONT_NAME
    r_univ.font.size = Pt(14)
    r_univ.font.bold = True

    r_date = p_col.add_run("NOVEMBER 2026")
    r_date.font.name = FONT_NAME
    r_date.font.size = Pt(14)
    r_date.font.bold = True

    doc.add_page_break()

def add_bonafide_certificate(doc):
    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_inst.paragraph_format.space_before = Pt(10)
    p_inst.paragraph_format.space_after = Pt(4)
    r = p_inst.add_run("ANNA UNIVERSITY : CHENNAI 600 025\n")
    r.font.name = FONT_NAME
    r.font.size = Pt(16)
    r.font.bold = True

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(8)
    p_title.paragraph_format.space_after = Pt(20)
    r = p_title.add_run("BONAFIDE CERTIFICATE")
    r.font.name = FONT_NAME
    r.font.size = Pt(16)
    r.font.bold = True

    p_text = doc.add_paragraph()
    p_text.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_text.paragraph_format.space_before = Pt(12)
    p_text.paragraph_format.space_after = Pt(24)
    p_text.paragraph_format.line_spacing = 2.0
    r = p_text.add_run(
        "Certified that this project report entitled \u201cCONVELINA: AN AI-POWERED IDENTITY "
        "DOCUMENT CONFLICT DETECTION AND GOVERNMENT CORRECTION ASSISTANCE SYSTEM USING LLMS AND RAG\u201d "
        "is the bonafide work of \u201cAJAY M (113023243003), ADITHYA B (113023243002), KAMESH G (113023243041)\u201d "
        "who carried out the project work under my supervision."
    )
    r.font.name = FONT_NAME
    r.font.size = Pt(14)

    # Two column table for signatures
    tbl = doc.add_table(rows=1, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    cell_l = tbl.rows[0].cells[0]
    cell_r = tbl.rows[0].cells[1]
    cell_l.width = Inches(2.85)
    cell_r.width = Inches(2.85)

    p_l = cell_l.paragraphs[0]
    p_l.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_l.paragraph_format.line_spacing = 1.2
    r_l = p_l.add_run(
        "<<Signature of Head of Department>>\nSIGNATURE\n\n\n\n"
        "Dr. SATHISH KUMAR S\n"
        "HEAD OF THE DEPARTMENT\n"
        "Assistant Professor & Head\n"
        "Department of AI & DS\n"
        "Vel Tech High Tech Dr. Rangarajan\n"
        "Dr. Sakunthala Engineering College\n"
        "Avadi, Chennai \u2013 600 062"
    )
    r_l.font.name = FONT_NAME
    r_l.font.size = Pt(11)

    p_r = cell_r.paragraphs[0]
    p_r.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_r.paragraph_format.line_spacing = 1.2
    # NOTE: Exactly as user requested: PROFESSOR (not Associate Professor!)
    r_r = p_r.add_run(
        "<<Signature of Supervisor>>\nSIGNATURE\n\n\n\n"
        "Dr. ZULAIKHA BEEVI S\n"
        "SUPERVISOR\n"
        "Professor\n"
        "Department of AI & DS\n"
        "Vel Tech High Tech Dr. Rangarajan\n"
        "Dr. Sakunthala Engineering College\n"
        "Avadi, Chennai \u2013 600 062"
    )
    r_r.font.name = FONT_NAME
    r_r.font.size = Pt(11)

    p_exam = doc.add_paragraph()
    p_exam.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_exam.paragraph_format.space_before = Pt(36)
    p_exam.paragraph_format.space_after = Pt(0)
    p_exam.paragraph_format.line_spacing = 1.3
    r_ex = p_exam.add_run(
        "Submitted for the ODD Semester Examination held on ............................... at "
        "Vel Tech High Tech Dr. Rangarajan Dr. Sakunthala Engineering College, Avadi, Chennai \u2013 600 062."
    )
    r_ex.font.name = FONT_NAME
    r_ex.font.size = Pt(11)

    doc.add_page_break()

def add_certificate_of_evaluation(doc):
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(10)
    p_title.paragraph_format.space_after = Pt(14)
    r = p_title.add_run("CERTIFICATE OF EVALUATION")
    r.font.name = FONT_NAME
    r.font.size = Pt(16)
    r.font.bold = True

    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_meta.paragraph_format.space_before = Pt(4)
    p_meta.paragraph_format.space_after = Pt(14)
    p_meta.paragraph_format.line_spacing = 1.3
    meta_text = (
        "College Name : Vel Tech High Tech Dr. Rangarajan Dr. Sakunthala Engineering College\n"
        "Degree       : Bachelor of Technology\n"
        "Branch       : Artificial Intelligence and Data Science\n"
        "Semester     : VII"
    )
    r_meta = p_meta.add_run(meta_text)
    r_meta.font.name = FONT_NAME
    r_meta.font.size = Pt(13)

    # Evaluation table
    tbl = doc.add_table(rows=4, cols=6)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    hdrs = ["S.No", "Name of the\nStudents", "Title of the\nProject", "Name, Designation &\nDept of Supervisor", "PO & PSO\nMapping", "SDG\nMapping"]
    col_w = [Inches(0.6), Inches(1.2), Inches(1.5), Inches(1.3), Inches(0.9), Inches(0.7)]
    for i, h in enumerate(hdrs):
        cell = tbl.rows[0].cells[i]
        cell.text = h
        cell.width = col_w[i]
        shading = parse_xml(r'<w:shd {} w:fill="1E3A8A"/>'.format(nsdecls('w')))
        cell._tc.get_or_add_tcPr().append(shading)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.name = FONT_NAME
            r.font.size = Pt(9.5)
            r.font.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)

    cands_data = [
        ("01.", "Ajay M\n(113023243003)"),
        ("02.", "Adithya B\n(113023243002)"),
        ("03.", "Kamesh G\n(113023243041)")
    ]
    for idx, (sno, cname) in enumerate(cands_data):
        row = tbl.rows[idx + 1]
        for c in range(6):
            row.cells[c].width = col_w[c]
        row.cells[0].text = sno
        row.cells[1].text = cname
        if idx == 0:
            row.cells[2].text = "CONVELINA: An AI-Powered Identity Document Conflict Detection and Government Correction Assistance System Using LLMs and RAG"
            row.cells[3].text = "Dr. Zulaikha Beevi S\nProfessor\nDepartment of AI & DS"
            row.cells[4].text = "POs: 1, 2, 3, 4,\n5, 6, 8, 9, 10,\n11, 12\nPSOs: 1, 2"
            row.cells[5].text = "SDG 9\nSDG 11\nSDG 16\nSDG 17"
        else:
            row.cells[2].text = "—"
            row.cells[3].text = "—"
            row.cells[4].text = "—"
            row.cells[5].text = "—"

    # Merge cells vertically for shared project details
    tbl.rows[1].cells[2].merge(tbl.rows[2].cells[2]).merge(tbl.rows[3].cells[2])
    tbl.rows[1].cells[3].merge(tbl.rows[2].cells[3]).merge(tbl.rows[3].cells[3])
    tbl.rows[1].cells[4].merge(tbl.rows[2].cells[4]).merge(tbl.rows[3].cells[4])
    tbl.rows[1].cells[5].merge(tbl.rows[2].cells[5]).merge(tbl.rows[3].cells[5])

    for r_idx in range(1, 4):
        for c_idx in range(6):
            p = tbl.rows[r_idx].cells[c_idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.name = FONT_NAME
                r.font.size = Pt(9.5)

    p_conf = doc.add_paragraph()
    p_conf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_conf.paragraph_format.space_before = Pt(16)
    p_conf.paragraph_format.space_after = Pt(28)
    p_conf.paragraph_format.line_spacing = 1.3
    r_c = p_conf.add_run(
        "The report of the project work submitted by the above students in partial fulfilment for the award "
        "of degree, Bachelor of Technology in Artificial Intelligence and Data Science for the viva voce "
        "examination held at Vel Tech High Tech Dr. Rangarajan Dr. Sakunthala Engineering College on "
        "___________________ has been evaluated and confirmed to be reports of the work done by the above students."
    )
    r_c.font.name = FONT_NAME
    r_c.font.size = Pt(12)

    # Examiner signatures
    tbl_ex = doc.add_table(rows=1, cols=2)
    tbl_ex.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_ex.autofit = False
    c_int = tbl_ex.rows[0].cells[0]
    c_ext = tbl_ex.rows[0].cells[1]
    c_int.width = Inches(2.85)
    c_ext.width = Inches(2.85)

    p_int = c_int.paragraphs[0]
    p_int.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r_int = p_int.add_run("<<Signature>>\nINTERNAL EXAMINER")
    r_int.font.name = FONT_NAME
    r_int.font.size = Pt(12)
    r_int.font.bold = True

    p_ext = c_ext.paragraphs[0]
    p_ext.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_ext = p_ext.add_run("<<Signature>>\nEXTERNAL EXAMINER")
    r_ext.font.name = FONT_NAME
    r_ext.font.size = Pt(12)
    r_ext.font.bold = True

    doc.add_page_break()

def add_acknowledgement(doc):
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(10)
    p_title.paragraph_format.space_after = Pt(16)
    r = p_title.add_run("ACKNOWLEDGEMENT")
    r.font.name = FONT_NAME
    r.font.size = Pt(16)
    r.font.bold = True

    paras = [
        "We wish to express our heartfelt gratitude and sincere thanks to all those who extended their "
        "generous help, guidance, and encouragement during our Project Phase \u2013 I work.",

        "First and foremost, we would like to convey our deepest gratitude and respect to our esteemed "
        "Founder President and Chairman, Col. Prof. Dr. Vel. Shri. R. Rangarajan, B.E (EEE), B.E (Mech), "
        "M.S (Auto), our revered Foundress President and Vice Chairman, Late Dr. Mrs. Sakunthala Rangarajan, "
        "M.B.B.S., our respected Chairperson and Managing Trustee, Dr. (Mrs.) Rangarajan Mahalakshmi Kishore, "
        "B.E., M.B.A (UK), Ph.D., and our Dynamic Director, Mr. K. V. D. Kishore Kumar, B.E., M.B.A (US), "
        "for their visionary leadership, kind encouragement, and continuous institutional support. Their inspiring "
        "guidance has been an enduring source of strength throughout this project.",

        "Our sincere thanks to our honourable Principal, Prof. Dr. E. Kamalanaban, B.E (CSE), M.E (CSE), "
        "Ph.D., for his continuous administrative support, academic leadership, and motivation during this "
        "Project Phase \u2013 I.",

        "We are deeply grateful to our Dean Academics, Prof. Dr. V. R. Ravi, B.E., M.E., Ph.D., and our Dean of "
        "PPT, Dr. J. B. Veeramalini, M.Tech., Ph.D., and Associate Dean of PPT, Dr. Chembian W T, M.E., Ph.D., "
        "for providing an environment that fosters technical rigor, innovation, and disciplined engineering methodology.",

        "We express our profound thanks to Dr. S. Sathish Kumar, Assistant Professor and Head of the Department "
        "of Artificial Intelligence and Data Science, for his sustained encouragement, administrative oversight, "
        "and guidance throughout the progression of this work.",

        "We extend our sincere and special thanks to our Project Supervisor, Dr. Zulaikha Beevi S, Professor, "
        "Department of Artificial Intelligence and Data Science, for her expert technical guidance, perceptive insights, "
        "rigorous evaluations, and constant encouragement throughout the formulation and development of this Phase I design.",

        "Finally, we express our heartfelt appreciation to all our faculty members and non-teaching staff for "
        "their assistance, and to our parents and family members for their unwavering support, moral encouragement, "
        "and belief in our academic endeavors throughout this journey."
    ]

    for p_text in paras:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.5
        r = p.add_run(p_text)
        r.font.name = FONT_NAME
        r.font.size = Pt(14)

    doc.add_page_break()

def add_abstract(doc):
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(10)
    p_title.paragraph_format.space_after = Pt(16)
    r = p_title.add_run("ABSTRACT")
    r.font.name = FONT_NAME
    r.font.size = Pt(16)
    r.font.bold = True

    paras = [
        "Foundational identification systems in India, including Aadhaar administered by the Unique "
        "Identification Authority of India (UIDAI), Permanent Account Numbers (PAN) issued by the Income Tax "
        "Department, Passports governed by the Ministry of External Affairs (MEA), and Universal Account Numbers (UAN) "
        "managed by the Employees' Provident Fund Organisation (EPFO), form an essential civic infrastructure. However, "
        "because these identity systems operate under distinct statutory mandates, differing regional transliteration "
        "conventions, and uncoordinated clerical data-entry practices, millions of citizens suffer from subtle demographic "
        "discrepancies. Common errors include expanded patronymic initials, phonetic spelling variants, inverted calendar "
        "dates of birth, and minor parental name discrepancies. When citizens seek passport verification, EPFO pension "
        "disbursements, or banking KYC onboarding, automated validation algorithms fail, triggering frequent application "
        "rejections and prolonged administrative delays.",

        "This project presents CONVELINA, an intelligent, privacy-conscious civic identity document conflict detection "
        "and government correction assistance system. CONVELINA integrates layout-aware optical character recognition (OCR) "
        "with automated Aadhaar demographic masking and Fernet encryption, satisfying Section 29 of the Aadhaar Act 2016. "
        "A multi-algorithmic Conflict Detection Engine leverages Jaro-Winkler prefix alignment, Levenshtein edit distance, "
        "and token sort heuristics to detect nuanced clerical variances without misclassifying honest discrepancies as fraud. "
        "A hallucination-resistant Retrieval-Augmented Generation (RAG) assistant, powered by dense vector representations "
        "indexed in an in-process Qdrant vector engine with a strict similarity floor of 0.55, provides citizens with "
        "verifiable statutory guidance. The system automates the synthesis of standardized legal instruments, including "
        "bilingual sworn affidavits attested with internal Ed25519 digital signatures and verifiable QR codes. Tenant isolation "
        "is enforced via PostgreSQL forced Row-Level Security (RLS) under a dedicated application role, and an append-only "
        "SHA-256 hash-chained audit ledger guarantees evidentiary integrity under the Bharatiya Sakshya Adhiniyam 2023."
    ]

    for p_text in paras:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.5
        r = p.add_run(p_text)
        r.font.name = FONT_NAME
        r.font.size = Pt(14)

    p_kw = doc.add_paragraph()
    p_kw.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_kw.paragraph_format.space_before = Pt(10)
    p_kw.paragraph_format.space_after = Pt(0)
    p_kw.paragraph_format.line_spacing = 1.5
    r_kwh = p_kw.add_run("Keywords: ")
    r_kwh.font.name = FONT_NAME
    r_kwh.font.size = Pt(14)
    r_kwh.font.bold = True
    r_kwt = p_kw.add_run("Artificial Intelligence, Identity Verification, Conflict Detection, Large Language Models, Retrieval-Augmented Generation, Row-Level Security, Public Key Infrastructure, e-Governance.")
    r_kwt.font.name = FONT_NAME
    r_kwt.font.size = Pt(14)
    r_kwt.font.italic = True

    doc.add_page_break()

def add_table_of_contents(doc, toc_entries):
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(10)
    p_title.paragraph_format.space_after = Pt(14)
    r = p_title.add_run("TABLE OF CONTENTS")
    r.font.name = FONT_NAME
    r.font.size = Pt(16)
    r.font.bold = True

    tbl = doc.add_table(rows=len(toc_entries) + 1, cols=3)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    col_w = [Inches(1.2), Inches(3.9), Inches(0.9)]
    for row in tbl.rows:
        for i, w in enumerate(col_w):
            row.cells[i].width = w

    # Header
    tbl.rows[0].cells[0].text = "CHAPTER NO."
    tbl.rows[0].cells[1].text = "TITLE"
    tbl.rows[0].cells[2].text = "PAGE NO."
    for i in range(3):
        p = tbl.rows[0].cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i != 1 else WD_ALIGN_PARAGRAPH.LEFT
        for r in p.runs:
            r.font.name = FONT_NAME
            r.font.size = Pt(11)
            r.font.bold = True

    for idx, (cno, title, pno, is_bold, indent) in enumerate(toc_entries):
        row = tbl.rows[idx + 1]
        row.cells[0].text = cno
        row.cells[1].text = ("    " * indent) + title
        row.cells[2].text = str(pno)

        p0 = row.cells[0].paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p0.paragraph_format.space_before = Pt(2)
        p0.paragraph_format.space_after = Pt(2)
        p0.paragraph_format.line_spacing = 1.15
        if p0.runs:
            p0.runs[0].font.name = FONT_NAME
            p0.runs[0].font.size = Pt(11)
            p0.runs[0].font.bold = is_bold

        p1 = row.cells[1].paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p1.paragraph_format.space_before = Pt(2)
        p1.paragraph_format.space_after = Pt(2)
        p1.paragraph_format.line_spacing = 1.15
        if p1.runs:
            p1.runs[0].font.name = FONT_NAME
            p1.runs[0].font.size = Pt(11)
            p1.runs[0].font.bold = is_bold

        p2 = row.cells[2].paragraphs[0]
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p2.paragraph_format.space_before = Pt(2)
        p2.paragraph_format.space_after = Pt(2)
        p2.paragraph_format.line_spacing = 1.15
        if p2.runs:
            p2.runs[0].font.name = FONT_NAME
            p2.runs[0].font.size = Pt(11)
            p2.runs[0].font.bold = is_bold

    doc.add_page_break()

def add_list_of_tables_page(doc, tables_list):
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(10)
    p_title.paragraph_format.space_after = Pt(14)
    r = p_title.add_run("LIST OF TABLES")
    r.font.name = FONT_NAME
    r.font.size = Pt(16)
    r.font.bold = True

    tbl = doc.add_table(rows=len(tables_list) + 1, cols=3)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    col_w = [Inches(1.2), Inches(3.9), Inches(0.9)]
    for row in tbl.rows:
        for i, w in enumerate(col_w):
            row.cells[i].width = w

    tbl.rows[0].cells[0].text = "TABLE NO."
    tbl.rows[0].cells[1].text = "TITLE"
    tbl.rows[0].cells[2].text = "PAGE NO."
    for i in range(3):
        p = tbl.rows[0].cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i != 1 else WD_ALIGN_PARAGRAPH.LEFT
        for r in p.runs:
            r.font.name = FONT_NAME
            r.font.size = Pt(11)
            r.font.bold = True

    for idx, (tno, title, pno) in enumerate(tables_list):
        row = tbl.rows[idx + 1]
        row.cells[0].text = tno
        row.cells[1].text = title
        row.cells[2].text = str(pno)

        for c_idx in range(3):
            p = row.cells[c_idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx != 1 else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            if p.runs:
                p.runs[0].font.name = FONT_NAME
                p.runs[0].font.size = Pt(11)

    doc.add_page_break()

def add_list_of_figures_page(doc, figures_list):
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(10)
    p_title.paragraph_format.space_after = Pt(14)
    r = p_title.add_run("LIST OF FIGURES")
    r.font.name = FONT_NAME
    r.font.size = Pt(16)
    r.font.bold = True

    tbl = doc.add_table(rows=len(figures_list) + 1, cols=3)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    col_w = [Inches(1.2), Inches(3.9), Inches(0.9)]
    for row in tbl.rows:
        for i, w in enumerate(col_w):
            row.cells[i].width = w

    tbl.rows[0].cells[0].text = "FIG. NO."
    tbl.rows[0].cells[1].text = "TITLE"
    tbl.rows[0].cells[2].text = "PAGE NO."
    for i in range(3):
        p = tbl.rows[0].cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i != 1 else WD_ALIGN_PARAGRAPH.LEFT
        for r in p.runs:
            r.font.name = FONT_NAME
            r.font.size = Pt(11)
            r.font.bold = True

    for idx, (fno, title, pno) in enumerate(figures_list):
        row = tbl.rows[idx + 1]
        row.cells[0].text = fno
        row.cells[1].text = title
        row.cells[2].text = str(pno)

        for c_idx in range(3):
            p = row.cells[c_idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx != 1 else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            if p.runs:
                p.runs[0].font.name = FONT_NAME
                p.runs[0].font.size = Pt(11)

    doc.add_page_break()

def add_list_of_abbreviations_page(doc, abbreviations_list):
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(10)
    p_title.paragraph_format.space_after = Pt(14)
    r = p_title.add_run("LIST OF ABBREVIATIONS AND NOMENCLATURE")
    r.font.name = FONT_NAME
    r.font.size = Pt(16)
    r.font.bold = True

    tbl = doc.add_table(rows=len(abbreviations_list) + 1, cols=3)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    col_w = [Inches(0.8), Inches(1.8), Inches(3.4)]
    for row in tbl.rows:
        for i, w in enumerate(col_w):
            row.cells[i].width = w

    tbl.rows[0].cells[0].text = "S.NO"
    tbl.rows[0].cells[1].text = "ABBREVIATION"
    tbl.rows[0].cells[2].text = "EXPANSION / MEANING"
    for i in range(3):
        p = tbl.rows[0].cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i != 2 else WD_ALIGN_PARAGRAPH.LEFT
        for r in p.runs:
            r.font.name = FONT_NAME
            r.font.size = Pt(11)
            r.font.bold = True

    for idx, (sno, abbr, meaning) in enumerate(abbreviations_list):
        row = tbl.rows[idx + 1]
        row.cells[0].text = sno
        row.cells[1].text = abbr
        row.cells[2].text = meaning

        for c_idx in range(3):
            p = row.cells[c_idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx != 2 else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            if p.runs:
                p.runs[0].font.name = FONT_NAME
                p.runs[0].font.size = Pt(11)

    doc.add_page_break()


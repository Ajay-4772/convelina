# -*- coding: utf-8 -*-
"""
Formatting styles and helpers for the CONVELINA Phase I Academic Report.
Calibrated for optimal layout density to achieve ~60 main-content pages:
- Paper: A4 (8.27 x 11.69 in)
- Margins: Left 1.5 in (38.1 mm), Right 1.0 in, Top 1.0 in, Bottom 1.0 in
- Font: Times New Roman
- Body: 14 pt, 1.35 line spacing, justified, 3 pt space after
- Figures: 4.7 in width, compact captions
- Tables & Algorithms: Compact padding and styled headers
"""

import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

FONT_NAME = "Times New Roman"
COLOR_BLACK = RGBColor(0, 0, 0)
COLOR_NAVY = RGBColor(15, 23, 42)

def setup_document_margins(section):
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.5)  # 38 mm for binding
    section.right_margin = Inches(1.0)

def add_page_number_to_run(run):
    fldSimple = OxmlElement('w:fldSimple')
    fldSimple.set(qn('w:instr'), 'PAGE')
    run._r.append(fldSimple)

def set_section_paging(section, num_fmt="decimal", start_num=1):
    sectPr = section._sectPr
    for child in list(sectPr):
        if child.tag.endswith('pgNumType'):
            sectPr.remove(child)
    pgNumType = OxmlElement('w:pgNumType')
    pgNumType.set(qn('w:fmt'), num_fmt)
    if start_num is not None:
        pgNumType.set(qn('w:start'), str(start_num))
    sectPr.append(pgNumType)

def add_chapter_title(doc, chapter_num, title_text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.25
    run1 = p.add_run(f"CHAPTER {chapter_num}\n")
    run1.font.name = FONT_NAME
    run1.font.size = Pt(18)
    run1.font.bold = True
    run1.font.color.rgb = COLOR_BLACK

    run2 = p.add_run(title_text.upper())
    run2.font.name = FONT_NAME
    run2.font.size = Pt(18)
    run2.font.bold = True
    run2.font.color.rgb = COLOR_BLACK
    return p

def add_heading_1(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.25
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = FONT_NAME
    run.font.size = Pt(16)
    run.font.bold = True
    run.font.color.rgb = COLOR_BLACK
    return p

def add_heading_2(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.25
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = FONT_NAME
    run.font.size = Pt(14)
    run.font.bold = True
    run.font.color.rgb = COLOR_BLACK
    return p

def add_heading_3(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.25
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = FONT_NAME
    run.font.size = Pt(14)
    run.font.bold = True
    run.font.italic = True
    run.font.color.rgb = COLOR_BLACK
    return p

def add_body_paragraph(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.25
    run = p.add_run(text)
    run.font.name = FONT_NAME
    run.font.size = Pt(14)
    run.font.color.rgb = COLOR_BLACK
    return p

def add_figure_block(doc, image_path, fig_num_str, caption_text, width=Inches(3.8)):
    if os.path.exists(image_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(6)
        p_img.paragraph_format.space_after = Pt(2)
        run_img = p_img.add_run()
        run_img.add_picture(image_path, width=width)
    
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(2)
    p_cap.paragraph_format.space_after = Pt(6)
    p_cap.paragraph_format.keep_with_next = False
    
    run_bold = p_cap.add_run(f"Figure {fig_num_str}: ")
    run_bold.font.name = FONT_NAME
    run_bold.font.size = Pt(11)
    run_bold.font.bold = True
    
    run_text = p_cap.add_run(caption_text)
    run_text.font.name = FONT_NAME
    run_text.font.size = Pt(11)
    run_text.font.italic = True

def add_table_block(doc, table_num_str, caption_text, headers, rows, col_widths=None):
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(8)
    p_cap.paragraph_format.space_after = Pt(3)
    p_cap.paragraph_format.keep_with_next = True
    
    run_bold = p_cap.add_run(f"Table {table_num_str}: ")
    run_bold.font.name = FONT_NAME
    run_bold.font.size = Pt(11)
    run_bold.font.bold = True
    
    run_text = p_cap.add_run(caption_text)
    run_text.font.name = FONT_NAME
    run_text.font.size = Pt(11)
    run_text.font.bold = True

    table = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    hdr_cells = table.rows[0].cells
    for i, header_text in enumerate(headers):
        hdr_cells[i].text = header_text
        shading = parse_xml(r'<w:shd {} w:fill="1E3A8A"/>'.format(nsdecls('w')))
        hdr_cells[i]._tc.get_or_add_tcPr().append(shading)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.05
        for r in p.runs:
            r.font.name = FONT_NAME
            r.font.size = Pt(10)
            r.font.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)

    for r_idx, row_data in enumerate(rows):
        row_cells = table.rows[r_idx + 1].cells
        bg_color = "F8FAFC" if (r_idx % 2 == 1) else "FFFFFF"
        for c_idx, cell_value in enumerate(row_data):
            row_cells[c_idx].text = str(cell_value)
            shading = parse_xml(r'<w:shd {} w:fill="{}"/>'.format(nsdecls('w'), bg_color))
            row_cells[c_idx]._tc.get_or_add_tcPr().append(shading)
            p = row_cells[c_idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.10
            for r in p.runs:
                r.font.name = FONT_NAME
                r.font.size = Pt(9.5)
                r.font.color.rgb = COLOR_BLACK

    if col_widths:
        for row in table.rows:
            for i, w in enumerate(col_widths):
                row.cells[i].width = w

    tblPr = table._tbl.tblPr
    borders = parse_xml(
        r'<w:tblBorders {} >'
        r'  <w:top w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>'
        r'  <w:left w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>'
        r'  <w:bottom w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>'
        r'  <w:right w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>'
        r'  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>'
        r'  <w:insideV w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>'
        r'</w:tblBorders>'.format(nsdecls('w'))
    )
    tblPr.append(borders)

    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_before = Pt(0)
    p_sp.paragraph_format.space_after = Pt(6)

def add_algorithm_box(doc, alg_num_str, title_text, input_text, output_text, steps_list):
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_cap.paragraph_format.space_before = Pt(8)
    p_cap.paragraph_format.space_after = Pt(3)
    p_cap.paragraph_format.keep_with_next = True
    
    r1 = p_cap.add_run(f"Algorithm {alg_num_str}: ")
    r1.font.name = FONT_NAME
    r1.font.size = Pt(11.5)
    r1.font.bold = True
    
    r2 = p_cap.add_run(title_text)
    r2.font.name = FONT_NAME
    r2.font.size = Pt(11.5)
    r2.font.bold = True

    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.rows[0].cells[0]
    cell.width = Inches(5.7)

    shading = parse_xml(r'<w:shd {} w:fill="F8FAFC"/>'.format(nsdecls('w')))
    cell._tc.get_or_add_tcPr().append(shading)
    borders = parse_xml(
        r'<w:tcBorders {} >'
        r'  <w:top w:val="single" w:sz="10" w:space="0" w:color="1E3A8A"/>'
        r'  <w:left w:val="single" w:sz="10" w:space="0" w:color="1E3A8A"/>'
        r'  <w:bottom w:val="single" w:sz="10" w:space="0" w:color="1E3A8A"/>'
        r'  <w:right w:val="single" w:sz="10" w:space="0" w:color="1E3A8A"/>'
        r'</w:tcBorders>'.format(nsdecls('w'))
    )
    cell._tc.get_or_add_tcPr().append(borders)

    p0 = cell.paragraphs[0]
    p0.paragraph_format.space_before = Pt(3)
    p0.paragraph_format.space_after = Pt(2)
    p0.paragraph_format.line_spacing = 1.05
    rin = p0.add_run(f"Input: {input_text}\nOutput: {output_text}\n")
    rin.font.name = "Consolas"
    rin.font.size = Pt(9)
    rin.font.bold = True
    rin.font.color.rgb = RGBColor(30, 58, 138)

    for i, step in enumerate(steps_list):
        p_step = cell.add_paragraph()
        p_step.paragraph_format.space_before = Pt(1)
        p_step.paragraph_format.space_after = Pt(1)
        p_step.paragraph_format.line_spacing = 1.05
        r_num = p_step.add_run(f"{i+1:02d}: ")
        r_num.font.name = "Consolas"
        r_num.font.size = Pt(8.5)
        r_num.font.bold = True
        r_num.font.color.rgb = RGBColor(100, 116, 139)
        
        r_txt = p_step.add_run(step)
        r_txt.font.name = "Consolas"
        r_txt.font.size = Pt(8.5)
        r_txt.font.color.rgb = COLOR_BLACK

    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_before = Pt(0)
    p_sp.paragraph_format.space_after = Pt(6)

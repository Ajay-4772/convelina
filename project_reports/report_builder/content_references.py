# -*- coding: utf-8 -*-
"""
REFERENCES section generator for CONVELINA Academic Report.
Adheres strictly to Anna University / Vel Tech High Tech format:
Alphabetical order by first author, single spacing, left justified.
Exactly 12 verified, peer-reviewed and statutory references.
"""

from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from .styles import FONT_NAME, COLOR_BLACK

def build_references(doc):
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(18)
    p_title.paragraph_format.space_after = Pt(16)
    r = p_title.add_run("REFERENCES")
    r.font.name = FONT_NAME
    r.font.size = Pt(18)
    r.font.bold = True

    references = [
        "1. Bernstein, D.J., Duif, N., Lange, T., Schwabe, P. and Yang, B.-Y. (2012) \u2018High-Speed High-Security Signatures\u2019, Journal of Cryptographic Engineering, Vol.2, No.2, pp.77\u201389.",
        "2. Fellegi, I.P. and Sunter, A.B. (1969) \u2018A Theory for Record Linkage\u2019, Journal of the American Statistical Association, Vol.64, No.328, pp.1183\u20131210.",
        "3. Jaro, M.A. (1989) \u2018Advances in Record-Linkage Methodology as Applied to Matching the 1985 Census of Tampa, Florida\u2019, Journal of the American Statistical Association, Vol.84, No.406, pp.414\u2013420.",
        "4. Ji, Z., Lee, N., Frieske, R., Yu, T., Su, D., Yan, X., Ishii, E., Bang, Y.J., Madotto, A. and Fung, P. (2023) \u2018Survey of Hallucination in Natural Language Generation\u2019, ACM Computing Surveys, Vol.55, No.12, pp.1\u201338.",
        "5. Levenshtein, V.I. (1966) \u2018Binary Codes Capable of Correcting Deletions, Insertions, and Reversals\u2019, Soviet Physics Doklady, Vol.10, No.8, pp.707\u2013710.",
        "6. Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., K\u00fcttler, H., Lewis, M., Yih, W., Rockt\u00e4schel, T., Riedel, S. and Kiela, D. (2020) \u2018Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks\u2019, Advances in Neural Information Processing Systems, Vol.33, pp.9459\u20139474.",
        "7. Malkov, Y.A. and Yashunin, D.A. (2020) \u2018Efficient and Robust Approximate Nearest Neighbor Search Using Hierarchical Navigable Small World Graphs\u2019, IEEE Transactions on Pattern Analysis and Machine Intelligence, Vol.42, No.4, pp.824\u2013836.",
        "8. Manning, C.D., Raghavan, P. and Sch\u00fctze, H. (2008) \u2018Introduction to Information Retrieval\u2019, Cambridge University Press, New York, pp.109\u2013133.",
        "9. Ministry of Law and Justice (2023) \u2018The Bharatiya Sakshya Adhiniyam, 2023 (Act No. 47 of 2023)\u2019, Gazette of India, Extraordinary, Part II, Section 1, New Delhi.",
        "10. Smith, R. (2007) \u2018An Overview of the Tesseract OCR Engine\u2019, Proc. Ninth Int. Conf. on Document Analysis and Recognition (ICDAR), Curitiba, Brazil, pp.629\u2013633.",
        "11. Unique Identification Authority of India (2016) \u2018The Aadhaar (Targeted Delivery of Financial and Other Subsidies, Benefits and Services) Act, 2016\u2019, Gazette of India, Extraordinary, Part II, Section 1, New Delhi.",
        "12. Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A.N., Kaiser, \u0141. and Polosukhin, I. (2017) \u2018Attention Is All You Need\u2019, Advances in Neural Information Processing Systems, Vol.30, pp.5998\u20136008."
    ]

    for ref in references:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.0  # Single spacing per format
        r = p.add_run(ref)
        r.font.name = FONT_NAME
        r.font.size = Pt(13)
        r.font.color.rgb = COLOR_BLACK


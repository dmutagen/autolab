import docx
from docx.shared import Mm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import re
from autolab.config import AppConfig

def normalize_dashes(text: str) -> str:
    """Replace long em-dashes (—) with middle en-dashes (–)."""
    if not text:
        return ""
    return text.replace("—", "–")

def clean_markdown(text: str) -> str:
    """Strip raw markdown artifacts like **bold**, `code`, and markdown headers."""
    if not text:
        return ""
    # Strip markdown code blocks
    text = re.sub(r'```[a-zA-Z]*\n?', '', text)
    text = text.replace('```', '')
    # Strip bold asterisks: **text** -> text
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    # Strip inline backticks: `code` -> code
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # Strip markdown headers: ### Header -> Header
    text = re.sub(r'^\s*#{1,6}\s+', '', text, flags=re.MULTILINE)
    return text.strip()

def normalize_paragraphs(text: str) -> List[str]:
    """
    Split text into coherent paragraphs and list items, un-wrapping artificial
    line breaks so that Word JUSTIFY does not stretch words across the entire page.
    Replaces all list bullets (*, •, -, +) with middle en-dashes (–).
    """
    if not text:
        return []

    clean_text = clean_markdown(normalize_dashes(text))
    raw_blocks = clean_text.split("\n\n")
    paragraphs = []

    for block in raw_blocks:
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if not lines:
            continue

        current = []
        for line in lines:
            # Replace bullet markers (*, •, +, -) with middle en-dash (–)
            line = re.sub(r'^[ \t]*[\*•\-\+][ \t]+', '– ', line)

            # Check if line starts a list item: '1. ', '1) ', '– '
            is_list_item = bool(re.match(r'^(?:\d+[\.\)]|–)\s+', line))
            if is_list_item:
                if current:
                    paragraphs.append(" ".join(current))
                    current = []
                current.append(line)
            else:
                if current:
                    current.append(line)
                else:
                    current.append(line)

        if current:
            paragraphs.append(" ".join(current))

    return paragraphs

def get_short_filename(subject: str, lab_number: str) -> str:
    """Generate short filenames matching the student's catalog: МОБ_5.docx, разраб2.docx, СУБД_1.docx, etc."""
    num_match = re.search(r'\d+(?:[\.\-_]\d+)?', str(lab_number))
    num = num_match.group(0) if num_match else "1"
    
    s = (subject or "").lower().strip()
    if any(w in s for w in ["трпо"]):
        return f"ТРПО_{num}.docx"
    elif any(w in s for w in ["дизайн", "design", "ui", "ux", "figma", "макет"]):
        return f"дизайн_{num}.docx"
    elif any(w in s for w in ["мобил", "android"]):
        return f"МОБ_{num}.docx"
    elif any(w in s for w in ["субд", "баз", "данн", "sql", "sqlite", "access"]):
        return f"СУБД_{num}.docx"
    elif any(w in s for w in ["защит"]):
        return f"защитакомп{num}.docx"
    elif any(w in s for w in ["иб", "безопасн"]):
        return f"ИБ_{num}.docx"
    elif any(w in s for w in ["схем"]):
        return f"схема{num}.docx"
    elif any(w in s for w in ["микро", "stm", "avr", "пмк"]):
        return f"прогмикро{num}.docx"
    elif any(w in s for w in ["практик"]):
        return f"практика_{num}.docx"
    elif any(w in s for w in ["разраб", "поит", "java", "программ"]):
        return f"разраб{num}.docx"
    else:
        words = re.findall(r'[A-Za-zА-Яа-яЁё]+', s)
        prefix = words[0][:6] if words else "лаб"
        return f"{prefix}_{num}.docx"

class DocxBuilder:
    def __init__(self, config: AppConfig):
        self.config = config
        self.doc = docx.Document()
        self._setup_document_geometry()
        self._setup_default_styles()

    def _setup_document_geometry(self):
        section = self.doc.sections[0]
        section.page_width = Mm(210)
        section.page_height = Mm(297)
        # Belarusian GOST: Left 30 mm, Right 10 mm, Top 20 mm, Bottom 20 mm
        section.left_margin = Mm(self.config.gost.margin_left_mm)
        section.right_margin = Mm(self.config.gost.margin_right_mm)
        section.top_margin = Mm(self.config.gost.margin_top_mm)
        section.bottom_margin = Mm(self.config.gost.margin_bottom_mm)

    def _setup_default_styles(self):
        style = self.doc.styles['Normal']
        style.font.name = 'Times New Roman'
        style.font.size = Pt(14)
        style.font.color.rgb = RGBColor(0, 0, 0)
        p_format = style.paragraph_format
        p_format.line_spacing = 1.0
        p_format.space_before = Pt(0)
        p_format.space_after = Pt(0)
        p_format.first_line_indent = Mm(self.config.gost.first_line_indent_cm * 10)
        p_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    def _add_paragraph(
        self,
        text: str = "",
        bold: bool = False,
        italic: bool = False,
        alignment: WD_ALIGN_PARAGRAPH = WD_ALIGN_PARAGRAPH.JUSTIFY,
        indent_cm: Optional[float] = None,
        font_size_pt: Optional[float] = None
    ):
        p = self.doc.add_paragraph()
        p.alignment = alignment
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        
        if indent_cm is not None:
            p.paragraph_format.first_line_indent = Mm(indent_cm * 10)
        else:
            if alignment == WD_ALIGN_PARAGRAPH.CENTER:
                p.paragraph_format.first_line_indent = Mm(0)
            else:
                p.paragraph_format.first_line_indent = Mm(self.config.gost.first_line_indent_cm * 10)

        if text:
            clean_text = clean_markdown(normalize_dashes(text))
            run = p.add_run(clean_text)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(font_size_pt or 14)
            if bold:
                run.bold = True
            if italic:
                run.italic = True
        return p

    def _add_text_block(self, text: str, bold: bool = False, prefix: str = ""):
        """Add multi-paragraph text cleanly without stretching line breaks."""
        paras = normalize_paragraphs(text)
        for i, p_text in enumerate(paras):
            full_text = f"{prefix}{p_text}" if i == 0 and prefix else p_text
            self._add_paragraph(full_text, bold=bold)

    def add_header(self, data: Dict[str, Any], user_variant: str = ""):
        lab_type = data.get("lab_type", "Лабораторная работа")
        lab_num = data.get("lab_number", "1")
        student = self.config.student
        
        # 1. Title: regular font, centered
        self._add_paragraph(
            f"{lab_type} № {lab_num}",
            alignment=WD_ALIGN_PARAGRAPH.CENTER,
            indent_cm=0
        )

        # 2. Metadata lines: regular font, 1.25 cm indent
        self._add_paragraph(f"Номер учебной группы: {student.group}")
        self._add_paragraph(f"Фамилия, инициалы обучающегося: {student.student_name}")
        
        raw_date = data.get("date") or ""
        if raw_date:
            if re.match(r'^\d{4}-\d{2}-\d{2}$', raw_date):
                parts = raw_date.split('-')
                date_str = f"{parts[2]}.{parts[1]}.{parts[0]}"
            else:
                date_str = raw_date
        else:
            date_str = datetime.now().strftime("%d.%m.%Y")
            
        self._add_paragraph(f"Дата выполнения работы: {date_str}")

        topic = clean_markdown(data.get("topic", "").strip("«»\" "))
        self._add_paragraph(f"Тема работы: «{topic}»")

        goal = clean_markdown(data.get("goal", "").strip())
        if goal:
            self._add_text_block(goal, prefix="Цель работы: ")

        task = clean_markdown(data.get("task", "").strip())
        if task:
            self._add_text_block(task, prefix="Задание: ")

        # ONLY add variant if user entered a variant explicitly on the site!
        clean_var = user_variant.strip() if user_variant else ""
        if clean_var and clean_var.lower() not in ["общий", "согласно заданию", "нет", "none", "-"]:
            self._add_paragraph(f"Вариант: {clean_var}")

        equip = clean_markdown(data.get("equipment", "").strip())
        if equip:
            self._add_text_block(equip, prefix="Оснащение работы: ")

    def add_code_block(self, code: str):
        self._add_paragraph("Код программы:")
        clean_code = code.strip()
        clean_code = re.sub(r'^```[a-zA-Z]*\n', '', clean_code)
        clean_code = re.sub(r'\n```$', '', clean_code)
        
        lines = clean_code.split("\n")
        for line in lines:
            p = self.doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.first_line_indent = Mm(0)
            
            run = p.add_run(line if line else " ")
            run.font.name = "Times New Roman"
            run.font.size = Pt(11)

    def add_screenshot(self, image_path: Path, figure_number: int, caption: str):
        if not image_path.exists():
            return

        p_img = self.doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.line_spacing = 1.0
        p_img.paragraph_format.space_before = Pt(0)
        p_img.paragraph_format.space_after = Pt(0)
        p_img.paragraph_format.first_line_indent = Mm(0)
        
        run_img = p_img.add_run()
        run_img.add_picture(str(image_path), width=Mm(160))

        clean_cap = clean_markdown(normalize_dashes(caption.strip(". ")))
        self._add_paragraph(
            f"Рисунок {figure_number} – {clean_cap}",
            alignment=WD_ALIGN_PARAGRAPH.CENTER,
            indent_cm=0,
            font_size_pt=14
        )

    def add_title_page(self, data: Dict[str, Any]):
        student = self.config.student
        
        self._add_paragraph("МИНИСТЕРСТВО ОБРАЗОВАНИЯ РЕСПУБЛИКИ БЕЛАРУСЬ", alignment=WD_ALIGN_PARAGRAPH.CENTER, indent_cm=0)
        self._add_paragraph(student.institution.upper(), alignment=WD_ALIGN_PARAGRAPH.CENTER, indent_cm=0)
        self._add_paragraph(f"Специальность {student.specialty}", alignment=WD_ALIGN_PARAGRAPH.CENTER, indent_cm=0)
        self._add_paragraph(f"Группа {student.group}", alignment=WD_ALIGN_PARAGRAPH.CENTER, indent_cm=0)

        for _ in range(3):
            self._add_paragraph("", indent_cm=0)

        lab_num = data.get("lab_number", "1")
        self._add_paragraph("ОТЧЕТ", alignment=WD_ALIGN_PARAGRAPH.CENTER, indent_cm=0, font_size_pt=16)
        self._add_paragraph(f"по лабораторной работе № {lab_num}", alignment=WD_ALIGN_PARAGRAPH.CENTER, indent_cm=0)
        
        topic = data.get("topic", "")
        if topic:
            self._add_paragraph(f"«{clean_markdown(topic)}»", alignment=WD_ALIGN_PARAGRAPH.CENTER, indent_cm=0)

        for _ in range(4):
            self._add_paragraph("", indent_cm=0)

        self._add_paragraph(f"Выполнил: обучающийся группы {student.group} {student.student_name}", indent_cm=8)
        self._add_paragraph(f"Принял: преподаватель {student.teacher_name}", indent_cm=8)

        for _ in range(4):
            self._add_paragraph("", indent_cm=0)

        self._add_paragraph(f"{student.city}  {student.year}", alignment=WD_ALIGN_PARAGRAPH.CENTER, indent_cm=0)
        self.doc.add_page_break()

    def build_report(
        self,
        data: Dict[str, Any],
        output_file: Path,
        screenshots: List[Path],
        with_title_page: bool = False,
        include_theory: bool = False,
        user_variant: str = ""
    ) -> Path:
        if with_title_page:
            self.add_title_page(data)

        self.add_header(data, user_variant=user_variant)

        # Section: Результаты выполнения работы
        self._add_paragraph("Результаты выполнения работы:")

        code = data.get("code", "").strip()
        sol_desc = data.get("solution_description", "").strip()

        if code:
            # Coding lab:
            if include_theory:
                theory = data.get("theory", "").strip()
                if theory:
                    self._add_text_block(theory)
                if sol_desc:
                    self._add_text_block(sol_desc)
            self.add_code_block(code)
        else:
            # Design / Non-coding lab (Figma, UI/UX, Schemes, Modeling):
            if include_theory:
                theory = data.get("theory", "").strip()
                if theory:
                    self._add_text_block(theory)
            if sol_desc:
                self._add_text_block(sol_desc)

        # Screenshots (can be multiple)
        fig_no = 1
        figures_meta = data.get("figures", [])
        for i, shot in enumerate(screenshots):
            cap = "Макет разработанного интерфейса" if not code else "Результат выполнения программы"
            if i < len(figures_meta) and "title" in figures_meta[i]:
                cap = figures_meta[i]["title"]
            elif len(screenshots) > 1:
                cap = f"Интерфейс программы (часть {i+1})"
            self.add_screenshot(shot, fig_no, cap)
            fig_no += 1

        # Control Questions
        qa_list = data.get("questions_answers", [])
        if qa_list:
            self._add_paragraph("Ответы на контрольные вопросы:")
            for i, qa in enumerate(qa_list):
                raw_q = clean_markdown(qa.get("question", "").strip())
                clean_q = re.sub(r'^\s*(\d+[\.\)]\s*)+', '', raw_q).strip()
                a = clean_markdown(qa.get("answer", "").strip())
                
                self._add_paragraph(f"{i+1}. {clean_q}")
                self._add_text_block(a)

        # Conclusion: Вывод
        concl = clean_markdown(data.get("conclusion", "").strip())
        if concl:
            if concl.lower().startswith("вывод:"):
                concl_text = concl[6:].strip()
            else:
                concl_text = concl
            self._add_paragraph(f"Вывод: {concl_text}")

        output_file.parent.mkdir(parents=True, exist_ok=True)
        self.doc.save(str(output_file))
        return output_file

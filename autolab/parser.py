import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from pypdf import PdfReader
import docx
from PIL import Image

class TaskParser:
    @staticmethod
    def parse_docx(path: Path) -> str:
        try:
            doc = docx.Document(path)
            full_text = []
            for p in doc.paragraphs:
                t = p.text.strip()
                if t:
                    full_text.append(t)
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join([c.text.strip() for c in row.cells if c.text.strip()])
                    if row_text:
                        full_text.append(row_text)
            return "\n".join(full_text)
        except Exception as e:
            return f"Ошибка чтения DOCX: {e}"

    @staticmethod
    def parse_pdf(path: Path) -> Tuple[str, List[Path]]:
        text_content = []
        image_paths = []
        try:
            reader = PdfReader(str(path))
            for i, page in enumerate(reader.pages):
                txt = page.extract_text() or ""
                if txt.strip():
                    text_content.append(f"--- Страница {i+1} ---\n{txt.strip()}")
            
            full_text = "\n\n".join(text_content)
            # If text is very short (e.g. scanned PDF), we can render pages to images if needed
            return full_text, image_paths
        except Exception as e:
            return f"Ошибка чтения PDF: {e}", image_paths

    @staticmethod
    def process_input(
        text_input: str = "",
        uploaded_file: Optional[Path] = None,
        variant: Optional[str] = None
    ) -> Dict[str, Any]:
        result = {
            "text": text_input.strip(),
            "images": [],
            "source_type": "text",
            "variant": variant or ""
        }

        if uploaded_file and uploaded_file.exists():
            suffix = uploaded_file.suffix.lower()
            if suffix in [".docx", ".doc"]:
                result["source_type"] = "docx"
                extracted = TaskParser.parse_docx(uploaded_file)
                result["text"] = (result["text"] + "\n\n" + extracted).strip()
            elif suffix == ".pdf":
                result["source_type"] = "pdf"
                extracted, images = TaskParser.parse_pdf(uploaded_file)
                result["text"] = (result["text"] + "\n\n" + extracted).strip()
                result["images"].extend(images)
            elif suffix in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]:
                result["source_type"] = "image"
                result["images"].append(uploaded_file)

        return result

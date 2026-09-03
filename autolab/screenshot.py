import os
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, List, Tuple
import re

class ScreenshotEngine:
    def __init__(self):
        self.font_mono_path = self._find_font([
            "/usr/share/fonts/TTF/JetBrainsMonoNL-Medium.ttf",
            "/usr/share/fonts/TTF/JetBrainsMonoNerdFont-Regular.ttf",
            "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
            "/usr/share/fonts/liberation/LiberationMono-Regular.ttf"
        ])
        self.font_sans_path = self._find_font([
            "/usr/share/fonts/noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
            "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/TTF/JetBrainsMonoNL-Medium.ttf"
        ])

    def _find_font(self, paths: List[str]) -> Optional[str]:
        for p in paths:
            if os.path.exists(p):
                return p
        return None

    def _get_font(self, size: int, mono: bool = True):
        font_path = self.font_mono_path if mono else self.font_sans_path
        if font_path:
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                pass
        return ImageFont.load_default()

    def render_terminal(
        self,
        command: str,
        output_text: str,
        output_image_path: Path,
        title: str = "Terminal — mugo@arch: ~/labs"
    ) -> Path:
        font = self._get_font(15, mono=True)
        small_font = self._get_font(13, mono=True)

        raw_lines = output_text.strip().split("\n")
        wrapped_lines = []
        max_cols = 85
        for line in raw_lines:
            if len(line) > max_cols:
                wrapped_lines.extend(textwrap.wrap(line, width=max_cols))
            else:
                wrapped_lines.append(line)

        if len(wrapped_lines) > 35:
            wrapped_lines = wrapped_lines[:32] + ["... [вывод сокращен] ..."]

        line_height = 24
        header_height = 36
        padding = 20
        total_lines = len(wrapped_lines) + 2  # prompt + extra
        content_height = max(total_lines * line_height, 160)
        img_height = header_height + content_height + (padding * 2)
        img_width = 860

        img = Image.new("RGB", (img_width, img_height), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)

        # Header Bar
        draw.rectangle([(0, 0), (img_width, header_height)], fill=(45, 45, 45))
        # Window buttons
        btn_radius = 6
        draw.ellipse([(14, 12), (14 + btn_radius * 2, 12 + btn_radius * 2)], fill=(255, 95, 86))
        draw.ellipse([(34, 12), (34 + btn_radius * 2, 12 + btn_radius * 2)], fill=(255, 189, 46))
        draw.ellipse([(54, 12), (54 + btn_radius * 2, 12 + btn_radius * 2)], fill=(39, 201, 63))

        # Title
        draw.text((80, 10), title, fill=(180, 180, 180), font=small_font)

        # Body
        y = header_height + padding
        # Terminal prompt
        draw.text((padding, y), "mugo@arch:~/labs$ ", fill=(134, 239, 172), font=font)
        prompt_len = 165
        draw.text((padding + prompt_len, y), command, fill=(243, 244, 246), font=font)
        y += line_height + 4

        for line in wrapped_lines:
            color = (229, 231, 235)
            if "error" in line.lower() or "ошибка" in line.lower():
                color = (248, 113, 113)
            elif "success" in line.lower() or "успешно" in line.lower():
                color = (74, 222, 128)
            draw.text((padding, y), line, fill=color, font=font)
            y += line_height

        output_image_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(output_image_path))
        return output_image_path

    def render_mobile_screen(
        self,
        title: str,
        topic: str,
        code: str,
        output_image_path: Path
    ) -> Path:
        width, height = 400, 680
        img = Image.new("RGB", (width, height), (248, 250, 252))
        draw = ImageDraw.Draw(img)

        font_header = self._get_font(16, mono=False)
        font_body = self._get_font(13, mono=False)
        font_small = self._get_font(11, mono=False)

        # 1. Android Status Bar
        draw.rectangle([(0, 0), (width, 28)], fill=(15, 23, 42))
        draw.text((16, 6), "12:00", fill=(255, 255, 255), font=font_small)
        draw.text((width - 85, 6), "LTE  100%", fill=(255, 255, 255), font=font_small)

        # 2. Android App Toolbar
        draw.rectangle([(0, 28), (width, 84)], fill=(37, 99, 235))
        draw.text((20, 44), title[:28] if title else "Android App", fill=(255, 255, 255), font=font_header)

        # 3. Dynamic Card / Visual Area
        draw.rounded_rectangle([(24, 108), (width - 24, 340)], radius=12, fill=(255, 255, 255), outline=(226, 232, 240), width=1)
        
        # Center illustrative graphic
        center_x, center_y = width // 2, 200
        draw.ellipse([(center_x - 45, center_y - 45), (center_x + 45, center_y + 45)], fill=(219, 234, 254))
        draw.rounded_rectangle([(center_x - 20, center_y - 20), (center_x + 20, center_y + 20)], radius=6, fill=(37, 99, 235))
        draw.ellipse([(center_x - 8, center_y - 8), (center_x + 8, center_y + 8)], fill=(255, 255, 255))
        
        # Labels
        short_topic = topic[:45] if topic else "Демонстрация работы приложения"
        draw.text((44, 270), short_topic, fill=(30, 41, 59), font=font_body)
        draw.text((44, 298), "Статус: Активно • Выполнение успешно", fill=(16, 185, 129), font=font_small)

        # 4. Buttons
        buttons = ["Запустить анимацию", "Сброс / Reset"]
        btn_y = 364
        for i, b_text in enumerate(buttons):
            b_bg = (37, 99, 235) if i == 0 else (241, 245, 249)
            b_fg = (255, 255, 255) if i == 0 else (71, 85, 105)
            draw.rounded_rectangle([(24, btn_y), (width - 24, btn_y + 46)], radius=8, fill=b_bg)
            draw.text((width // 2 - len(b_text) * 3 - 10, btn_y + 14), b_text, fill=b_fg, font=font_body)
            btn_y += 58

        # 5. Bottom Navigation Bar
        nav_y = height - 48
        draw.rectangle([(0, nav_y), (width, height)], fill=(15, 23, 42))
        draw.polygon([(width//4 - 8, nav_y + 24), (width//4 + 6, nav_y + 14), (width//4 + 6, nav_y + 34)], fill=(203, 213, 225))
        draw.ellipse([(width//2 - 7, nav_y + 17), (width//2 + 7, nav_y + 31)], fill=(203, 213, 225))
        draw.rectangle([(3*width//4 - 7, nav_y + 17), (3*width//4 + 7, nav_y + 31)], fill=(203, 213, 225))

        output_image_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(output_image_path))
        return output_image_path

    def render_ui_wireframe(
        self,
        title: str,
        topic: str,
        output_image_path: Path
    ) -> Path:
        width, height = 900, 560
        img = Image.new("RGB", (width, height), (248, 250, 252))
        draw = ImageDraw.Draw(img)

        font_header = self._get_font(15, mono=False)
        font_body = self._get_font(13, mono=False)
        font_small = self._get_font(11, mono=False)

        # 1. Figma / Browser Frame Bar
        draw.rectangle([(0, 0), (width, 44)], fill=(226, 232, 240))
        draw.ellipse([(16, 16), (28, 28)], fill=(239, 68, 68))
        draw.ellipse([(36, 16), (48, 28)], fill=(245, 158, 11))
        draw.ellipse([(56, 16), (68, 28)], fill=(16, 185, 129))
        draw.rounded_rectangle([(100, 10), (width - 120, 34)], radius=6, fill=(255, 255, 255))
        draw.text((120, 14), f"Figma / Web Prototype — {topic[:50]}", fill=(100, 116, 139), font=font_small)

        # 2. Navigation Bar
        draw.rectangle([(0, 44), (width, 100)], fill=(255, 255, 255))
        draw.line([(0, 100), (width, 100)], fill=(226, 232, 240), width=1)
        draw.rounded_rectangle([(30, 58), (140, 86)], radius=6, fill=(37, 99, 235))
        draw.text((45, 64), "UI Project", fill=(255, 255, 255), font=font_body)
        links = ["Главная", "Разделы", "Компоненты", "Профиль"]
        for i, link in enumerate(links):
            draw.text((200 + i * 110, 66), link, fill=(71, 85, 105), font=font_body)
        draw.rounded_rectangle([(width - 160, 58), (width - 30, 86)], radius=6, fill=(16, 185, 129))
        draw.text((width - 135, 64), "Действие / CTA", fill=(255, 255, 255), font=font_body)

        # 3. Hero / Main Concept Section
        draw.rectangle([(0, 101), (width, 260)], fill=(241, 245, 249))
        draw.text((40, 125), topic[:55] if topic else "Разработка структуры пользовательского интерфейса", fill=(15, 23, 42), font=font_header)
        draw.text((40, 155), "Концепт интерактивного макета, адаптивная сетка (12-column grid) и дизайн-система", fill=(100, 116, 139), font=font_small)
        draw.rounded_rectangle([(40, 195), (180, 230)], radius=6, fill=(37, 99, 235))
        draw.text((65, 205), "Подробнее", fill=(255, 255, 255), font=font_body)
        draw.rounded_rectangle([(width - 320, 120), (width - 40, 245)], radius=10, fill=(255, 255, 255), outline=(203, 213, 225), width=2)
        draw.text((width - 240, 175), "UI Component Area", fill=(148, 163, 184), font=font_small)

        # 4. Content Cards Grid
        card_w = (width - 80 - 40) // 3
        for i in range(3):
            cx = 40 + i * (card_w + 20)
            cy = 280
            draw.rounded_rectangle([(cx, cy), (cx + card_w, cy + 160)], radius=8, fill=(255, 255, 255), outline=(226, 232, 240), width=1)
            draw.rounded_rectangle([(cx + 10, cy + 10), (cx + card_w - 10, cy + 80)], radius=6, fill=(241, 245, 249))
            draw.text((cx + card_w//2 - 35, cy + 40), f"Модуль {i+1}", fill=(100, 116, 139), font=font_small)
            draw.text((cx + 15, cy + 95), f"Элемент интерфейса №{i+1}", fill=(30, 41, 59), font=font_body)
            draw.text((cx + 15, cy + 120), "Сетка: 12 колонок / Auto-layout", fill=(148, 163, 184), font=font_small)

        # 5. Color Palette & Typography Footer
        draw.rectangle([(0, height - 70), (width, height)], fill=(255, 255, 255))
        draw.line([(0, height - 70), (width, height - 70)], fill=(226, 232, 240), width=1)
        draw.text((40, height - 50), "Цветовая палитра: ", fill=(71, 85, 105), font=font_body)
        palette = [
            ((37, 99, 235), "#2563EB Primary"),
            ((16, 185, 129), "#10B981 Success"),
            ((245, 158, 11), "#F59E0B Accent"),
            ((15, 23, 42), "#0F172A Dark")
        ]
        for i, (col, label) in enumerate(palette):
            bx = 180 + i * 160
            draw.rounded_rectangle([(bx, height - 54), (bx + 20, height - 34)], radius=4, fill=col)
            draw.text((bx + 26, height - 50), label, fill=(100, 116, 139), font=font_small)

        output_image_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(output_image_path))
        return output_image_path

    def render_smart_screenshot(
        self,
        subject: str,
        topic: str,
        code: str,
        command: str,
        output_text: str,
        output_image_path: Path
    ) -> Path:
        """Intelligently detects whether to render an Android screen, UI Wireframe, or Terminal window."""
        subj_lower = (subject or "").lower()
        code_lower = (code or "").lower()
        topic_lower = (topic or "").lower()

        is_design = (
            "дизайн" in subj_lower or
            "дизайн" in topic_lower or
            "design" in subj_lower or
            "design" in topic_lower or
            "figma" in subj_lower or
            "figma" in topic_lower or
            "макет" in subj_lower or
            "макет" in topic_lower or
            "ui" in subj_lower or
            "ux" in subj_lower or
            ("интерфейс" in topic_lower and not code.strip())
        )

        is_mobile = (
            "мобил" in subj_lower or
            "android" in subj_lower or
            "androidx" in code_lower or
            "import android" in code_lower or
            "setcontentview" in code_lower or
            "activity" in code_lower
        )

        if is_design:
            return self.render_ui_wireframe(
                title=subject or "UI/UX Design Mockup",
                topic=topic or "Разработка интерфейса пользователя",
                output_image_path=output_image_path
            )
        elif is_mobile:
            return self.render_mobile_screen(
                title=subject or "Android Application",
                topic=topic,
                code=code,
                output_image_path=output_image_path
            )
        else:
            return self.render_terminal(
                command=command,
                output_text=output_text,
                output_image_path=output_image_path,
                title=f"Terminal — mugo@arch: ~/labs"
            )

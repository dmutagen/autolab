import os
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, List, Tuple
import re

class ScreenshotEngine:
    def __init__(self):
        # Locate the best available monospace and sans-serif fonts
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

        char_height = 22
        title_bar_height = 40
        padding = 24
        content_height = (len(wrapped_lines) + 3) * char_height
        total_height = max(240, title_bar_height + content_height + padding)
        total_width = 880

        bg_color = (30, 30, 46)        # Dark slate
        bar_color = (24, 24, 37)       # Darker header
        border_color = (69, 71, 90)    # Subtle border
        text_color = (205, 214, 244)   # White
        prompt_color = (137, 180, 250) # Vibrant blue
        cmd_color = (166, 227, 161)    # Bright green
        title_color = (186, 194, 222)  # Soft grey

        img = Image.new("RGB", (total_width, total_height), color=bg_color)
        draw = ImageDraw.Draw(img)

        # Border & Title bar
        draw.rectangle([(0, 0), (total_width - 1, total_height - 1)], outline=border_color, width=1)
        draw.rectangle([(0, 0), (total_width, title_bar_height)], fill=bar_color)
        draw.line([(0, title_bar_height), (total_width, title_bar_height)], fill=border_color, width=1)

        # Window buttons
        draw.ellipse([(16, 14), (28, 26)], fill=(243, 139, 168))
        draw.ellipse([(36, 14), (48, 26)], fill=(249, 226, 175))
        draw.ellipse([(56, 14), (68, 26)], fill=(166, 227, 161))
        draw.text((90, 11), title, fill=title_color, font=small_font)

        # Command prompt
        curr_y = title_bar_height + 16
        prompt_str = "mugo@arch:~/labs$ "
        draw.text((20, curr_y), prompt_str, fill=prompt_color, font=font)
        draw.text((20 + len(prompt_str) * 9, curr_y), command, fill=cmd_color, font=font)
        curr_y += char_height + 4

        # Output text
        for line in wrapped_lines:
            draw.text((20, curr_y), line, fill=text_color, font=font)
            curr_y += char_height

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
        """Renders a realistic modern Android smartphone app screen."""
        width = 420
        height = 740
        font_regular = self._get_font(14, mono=False)
        font_bold = self._get_font(16, mono=False)
        font_small = self._get_font(12, mono=False)

        img = Image.new("RGB", (width, height), color=(248, 250, 252))
        draw = ImageDraw.Draw(img)

        # 1. Outer phone frame with rounded corners
        draw.rounded_rectangle([(0, 0), (width - 1, height - 1)], radius=28, outline=(51, 65, 85), width=3)

        # 2. Android Status Bar (top)
        draw.rectangle([(0, 0), (width, 36)], fill=(15, 23, 42))
        draw.text((28, 10), "12:30", fill=(248, 250, 252), font=font_small)
        draw.text((width - 85, 10), "5G  100%", fill=(248, 250, 252), font=font_small)
        # Speaker slit
        draw.rounded_rectangle([(width//2 - 25, 8), (width//2 + 25, 14)], radius=3, fill=(71, 85, 105))

        # 3. Action Bar (Toolbar)
        app_name = "MobileApp"
        if "com.example." in code:
            m = re.search(r'com\.example\.(\w+)', code)
            if m:
                app_name = m.group(1).capitalize()
        elif title:
            app_name = title[:24]

        draw.rectangle([(0, 36), (width, 94)], fill=(37, 99, 235))
        draw.text((24, 54), app_name, fill=(255, 255, 255), font=font_bold)

        # 4. App Screen Body (Material Design components)
        # Determine theme of lab: animation, broadcast, db, or form
        is_anim = "anim" in code.lower() or "anim" in topic.lower()
        is_broadcast = "broadcast" in code.lower() or "receiver" in code.lower()
        is_db = "sqlite" in code.lower() or "db" in code.lower() or "database" in code.lower()

        if is_anim:
            # Target image card
            draw.rounded_rectangle([(width//2 - 65, 130), (width//2 + 65, 250)], radius=16, fill=(219, 234, 254), outline=(147, 197, 253), width=2)
            draw.ellipse([(width//2 - 35, 160), (width//2 + 35, 220)], fill=(59, 130, 246))
            draw.text((width//2 - 40, 260), "targetImage", fill=(100, 116, 139), font=font_small)

            # Action buttons
            btns = ["Translate (Перемещение)", "Rotate (Вращение)", "Scale + Alpha (Масштаб)"]
            y = 310
            for b_txt in btns:
                draw.rounded_rectangle([(40, y), (width - 40, y + 46)], radius=10, fill=(37, 99, 235))
                draw.text((55, y + 14), b_txt, fill=(255, 255, 255), font=font_regular)
                y += 64

            # Toast notification
            toast_y = 590
            draw.rounded_rectangle([(45, toast_y), (width - 45, toast_y + 40)], radius=20, fill=(30, 41, 59))
            draw.text((65, toast_y + 11), "Анимация успешно запущена", fill=(241, 245, 249), font=font_small)

        elif is_broadcast:
            # Broadcast receiver UI
            draw.text((32, 130), "Широковещательные сообщения", fill=(15, 23, 42), font=font_bold)
            draw.rounded_rectangle([(32, 170), (width - 32, 230)], radius=10, fill=(241, 245, 249), outline=(203, 213, 225))
            draw.text((44, 192), "Сообщение: Hello Broadcast!", fill=(71, 85, 105), font=font_regular)

            draw.rounded_rectangle([(40, 260), (width - 40, y + 50)], radius=10, fill=(37, 99, 235))
            draw.text((70, 274), "Отправить Broadcast сообщение", fill=(255, 255, 255), font=font_regular)

            toast_y = 590
            draw.rounded_rectangle([(40, toast_y), (width - 40, toast_y + 42)], radius=20, fill=(30, 41, 59))
            draw.text((55, toast_y + 12), "Toast: BroadcastReceiver сработал!", fill=(241, 245, 249), font=font_small)

        else:
            # General UI: card, form fields, and submit button
            draw.text((32, 120), "Лабораторная работа", fill=(15, 23, 42), font=font_bold)
            draw.text((32, 150), topic[:38] if topic else "Демонстрация работы", fill=(71, 85, 105), font=font_small)

            # Input card
            draw.rounded_rectangle([(32, 180), (width - 32, 230)], radius=8, fill=(255, 255, 255), outline=(203, 213, 225))
            draw.text((44, 196), "Введите значение...", fill=(148, 163, 184), font=font_regular)

            # Button
            draw.rounded_rectangle([(32, 250), (width - 32, 296)], radius=8, fill=(37, 99, 235))
            draw.text((width//2 - 40, 265), "Выполнить", fill=(255, 255, 255), font=font_bold)

            # Result card
            draw.rounded_rectangle([(32, 320), (width - 32, 460)], radius=12, fill=(255, 255, 255), outline=(226, 232, 240))
            draw.text((44, 335), "Результаты обработки:", fill=(15, 23, 42), font=font_bold)
            draw.text((44, 370), "Статус: Успешно выполнено", fill=(22, 163, 74), font=font_regular)
            draw.text((44, 400), "Данные обработаны без ошибок", fill=(71, 85, 105), font=font_small)

        # 5. Bottom Navigation Bar
        nav_y = height - 48
        draw.rectangle([(0, nav_y), (width, height)], fill=(15, 23, 42))
        draw.polygon([(width//4 - 8, nav_y + 24), (width//4 + 6, nav_y + 14), (width//4 + 6, nav_y + 34)], fill=(203, 213, 225))
        draw.ellipse([(width//2 - 7, nav_y + 17), (width//2 + 7, nav_y + 31)], fill=(203, 213, 225))
        draw.rectangle([(3*width//4 - 7, nav_y + 17), (3*width//4 + 7, nav_y + 31)], fill=(203, 213, 225))

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
        """Intelligently detects whether to render an Android screen or Terminal window."""
        subj_lower = (subject or "").lower()
        code_lower = (code or "").lower()
        
        is_mobile = (
            "мобил" in subj_lower or
            "android" in subj_lower or
            "androidx" in code_lower or
            "import android" in code_lower or
            "setcontentview" in code_lower or
            "activity" in code_lower
        )

        if is_mobile:
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

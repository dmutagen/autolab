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
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
            "/usr/share/fonts/noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/TTF/JetBrainsMonoNL-Medium.ttf"
        ])
        self.font_bold_path = self._find_font([
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/noto/NotoSans-Bold.ttf",
            "/usr/share/fonts/liberation/LiberationSans-Bold.ttf"
        ])

    def _find_font(self, paths: List[str]) -> Optional[str]:
        for p in paths:
            if os.path.exists(p):
                return p
        return None

    def _get_font(self, size: int, mono: bool = True, bold: bool = False):
        path = self.font_mono_path if mono else (self.font_bold_path if bold else self.font_sans_path)
        if path:
            try:
                return ImageFont.truetype(path, size)
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
        total_lines = len(wrapped_lines) + 2
        content_height = max(total_lines * line_height, 160)
        img_height = header_height + content_height + (padding * 2)
        img_width = 860

        img = Image.new("RGB", (img_width, img_height), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)

        # Header Bar
        draw.rectangle([(0, 0), (img_width, header_height)], fill=(45, 45, 45))
        btn_radius = 6
        draw.ellipse([(14, 12), (14 + btn_radius * 2, 12 + btn_radius * 2)], fill=(255, 95, 86))
        draw.ellipse([(34, 12), (34 + btn_radius * 2, 12 + btn_radius * 2)], fill=(255, 189, 46))
        draw.ellipse([(54, 12), (54 + btn_radius * 2, 12 + btn_radius * 2)], fill=(39, 201, 63))

        draw.text((80, 10), title, fill=(180, 180, 180), font=small_font)

        y = header_height + padding
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

    def _draw_android_frame(self, draw: ImageDraw.Draw, width: int, height: int, step_index: int, app_title: str):
        font_header = self._get_font(15, mono=False, bold=True)
        font_small = self._get_font(11, mono=False)

        # 1. Android Status Bar
        draw.rectangle([(0, 0), (width, 28)], fill=(15, 23, 42))
        draw.text((16, 6), f"12:{10 + step_index:02d}", fill=(255, 255, 255), font=font_small)
        draw.text((width - 85, 6), "LTE  100%", fill=(255, 255, 255), font=font_small)

        # 2. Android Toolbar
        draw.rectangle([(0, 28), (width, 84)], fill=(37, 99, 235))
        draw.text((20, 46), app_title[:30], fill=(255, 255, 255), font=font_header)

        # 3. Bottom Nav Bar
        nav_y = height - 48
        draw.rectangle([(0, nav_y), (width, height)], fill=(15, 23, 42))
        draw.polygon([(width//4 - 8, nav_y + 24), (width//4 + 6, nav_y + 14), (width//4 + 6, nav_y + 34)], fill=(203, 213, 225))
        draw.ellipse([(width//2 - 7, nav_y + 17), (width//2 + 7, nav_y + 31)], fill=(203, 213, 225))
        draw.rectangle([(3*width//4 - 7, nav_y + 17), (3*width//4 + 7, nav_y + 31)], fill=(203, 213, 225))

    def render_localization_screen(
        self,
        lang_code: str,
        output_image_path: Path,
        step_index: int = 1
    ) -> Path:
        width, height = 400, 680
        img = Image.new("RGB", (width, height), (248, 250, 252))
        draw = ImageDraw.Draw(img)

        font_header = self._get_font(15, mono=False, bold=True)
        font_body = self._get_font(13, mono=False)
        font_small = self._get_font(11, mono=False)
        font_bold = self._get_font(13, mono=False, bold=True)

        app_titles = {
            "ru": "Личные данные пользователя",
            "be": "Асабістыя дадзеныя",
            "en": "User Personal Profile",
            "res": "Результат сохранения"
        }
        app_title = app_titles.get(lang_code, "Мобильное приложение")
        self._draw_android_frame(draw, width, height, step_index, app_title)

        # Language Switcher Bar
        draw.text((24, 96), "Язык интерфейса / Language:", fill=(100, 116, 139), font=font_small)
        pills = [("ru", "Русский"), ("be", "Беларуская"), ("en", "English")]
        px = 24
        for p_code, p_name in pills:
            is_active = (p_code == lang_code)
            p_bg = (37, 99, 235) if is_active else (241, 245, 249)
            p_fg = (255, 255, 255) if is_active else (71, 85, 105)
            p_w = 110
            draw.rounded_rectangle([(px, 116), (px + p_w, 148)], radius=6, fill=p_bg)
            draw.text((px + 12, 125), f"{p_code.upper()} • {p_name[:8]}", fill=p_fg, font=font_small)
            px += p_w + 8

        # Card Content
        draw.rounded_rectangle([(24, 166), (width - 24, 460)], radius=12, fill=(255, 255, 255), outline=(226, 232, 240), width=1)

        if lang_code == "res":
            # Success result card
            draw.ellipse([(width // 2 - 32, 195), (width // 2 + 32, 259)], fill=(220, 252, 231))
            draw.text((width // 2 - 8, 214), "✓", fill=(16, 185, 129), font=font_header)
            draw.text((width // 2 - 95, 276), "Данные успешно сохранены", fill=(15, 23, 42), font=font_bold)
            draw.text((44, 315), "ФИО: Кашевич Евгений Николаевич", fill=(51, 65, 85), font=font_body)
            draw.text((44, 345), "Учебная группа: ПМ-31", fill=(51, 65, 85), font=font_body)
            draw.text((44, 375), "Текущая локаль: strings.xml (values-ru)", fill=(100, 116, 139), font=font_small)
            draw.text((44, 405), "Статус: Запись добавлена в базу данных", fill=(16, 185, 129), font=font_small)
            buttons = ("Назад в форму", "Редактировать профиль")
        else:
            field_data = {
                "ru": [("Имя пользователя", "Евгений"), ("Фамилия", "Кашевич"), ("Учебная группа", "ПМ-31")],
                "be": [("Імя карыстальніка", "Яўген"), ("Прозвішча", "Кашэвіч"), ("Вучэбная група", "ПМ-31")],
                "en": [("First Name", "Eugene"), ("Last Name", "Kashevich"), ("Study Group", "PM-31")]
            }.get(lang_code, [("Имя", "Евгений"), ("Группа", "ПМ-31")])

            fy = 186
            for lbl, val in field_data:
                draw.text((40, fy), lbl, fill=(100, 116, 139), font=font_small)
                draw.rounded_rectangle([(40, fy + 18), (width - 40, fy + 54)], radius=6, fill=(248, 250, 252), outline=(203, 213, 225), width=1)
                draw.text((52, fy + 27), val, fill=(15, 23, 42), font=font_body)
                fy += 66

            badge_text = {
                "ru": "Ресурсный каталог: res/values-ru/strings.xml",
                "be": "Рэсурсны каталог: res/values-be/strings.xml",
                "en": "Resource bundle: res/values-en/strings.xml"
            }.get(lang_code, "")
            draw.text((44, fy + 10), badge_text, fill=(37, 99, 235), font=font_small)

            btn_data = {
                "ru": ("Сохранить данные", "Очистить форму"),
                "be": ("Захаваць дадзеныя", "Ачысціць форму"),
                "en": ("Save Profile", "Clear Form")
            }
            buttons = btn_data.get(lang_code, ("Сохранить", "Сброс"))

        # Action Buttons
        b_y = 480
        draw.rounded_rectangle([(24, b_y), (width - 24, b_y + 44)], radius=8, fill=(37, 99, 235))
        draw.text((width // 2 - len(buttons[0]) * 4, b_y + 13), buttons[0], fill=(255, 255, 255), font=font_body)

        draw.rounded_rectangle([(24, b_y + 52), (width - 24, b_y + 96)], radius=8, fill=(241, 245, 249))
        draw.text((width // 2 - len(buttons[1]) * 4, b_y + 65), buttons[1], fill=(71, 85, 105), font=font_body)

        output_image_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(output_image_path))
        return output_image_path

    def render_animation_screen(
        self,
        anim_type: str,
        output_image_path: Path,
        step_index: int = 1
    ) -> Path:
        width, height = 400, 680
        img = Image.new("RGB", (width, height), (248, 250, 252))
        draw = ImageDraw.Draw(img)

        font_body = self._get_font(13, mono=False)
        font_small = self._get_font(11, mono=False)

        self._draw_android_frame(draw, width, height, step_index, "Animation Demo")

        draw.rounded_rectangle([(24, 108), (width - 24, 340)], radius=12, fill=(255, 255, 255), outline=(226, 232, 240), width=1)

        base_cx, base_cy = width // 2, 200
        toast_text = ""

        if anim_type == "translate":
            draw.ellipse([(base_cx - 35, base_cy - 35), (base_cx + 35, base_cy + 35)], outline=(203, 213, 225), width=2)
            draw.line([(base_cx, base_cy), (base_cx + 50, base_cy - 35)], fill=(37, 99, 235), width=2)
            cx, cy = base_cx + 50, base_cy - 35
            draw.ellipse([(cx - 40, cy - 40), (cx + 40, cy + 40)], fill=(219, 234, 254))
            draw.rounded_rectangle([(cx - 18, cy - 18), (cx + 18, cy + 18)], radius=6, fill=(37, 99, 235))
            draw.ellipse([(cx - 7, cy - 7), (cx + 7, cy + 7)], fill=(255, 255, 255))
            status_text = "Анимация: Перемещение (X: +50, Y: -35)"
            toast_text = "Toast: Translate animation completed"
        elif anim_type == "rotate":
            cx, cy = base_cx, base_cy
            draw.arc([(cx - 52, cy - 52), (cx + 52, cy + 52)], start=30, end=330, fill=(37, 99, 235), width=3)
            draw.ellipse([(cx - 45, cy - 45), (cx + 45, cy + 45)], fill=(254, 243, 199))
            draw.polygon([(cx, cy - 22), (cx + 22, cy), (cx, cy + 22), (cx - 22, cy)], fill=(245, 158, 11))
            draw.ellipse([(cx - 6, cy - 6), (cx + 6, cy + 6)], fill=(255, 255, 255))
            status_text = "Анимация: Вращение (Rotate 360° вокруг центра)"
            toast_text = "Toast: Rotate animation completed"
        elif anim_type == "scale":
            cx, cy = base_cx, base_cy
            draw.ellipse([(cx - 62, cy - 62), (cx + 62, cy + 62)], fill=(220, 252, 231))
            draw.rounded_rectangle([(cx - 28, cy - 28), (cx + 28, cy + 28)], radius=8, fill=(16, 185, 129))
            draw.ellipse([(cx - 11, cy - 11), (cx + 11, cy + 11)], fill=(255, 255, 255))
            status_text = "Анимация: Масштабирование (Увеличение 150%)"
            toast_text = "Toast: Scale animation (1.5x) completed"
        else:
            cx, cy = base_cx, base_cy
            draw.ellipse([(cx - 45, cy - 45), (cx + 45, cy + 45)], fill=(219, 234, 254))
            draw.rounded_rectangle([(cx - 20, cy - 20), (cx + 20, cy + 20)], radius=6, fill=(37, 99, 235))
            draw.ellipse([(cx - 8, cy - 8), (cx + 8, cy + 8)], fill=(255, 255, 255))
            status_text = "Статус: Готово к запуску анимации"

        draw.text((44, 275), "Элемент анимации: ImageView", fill=(30, 41, 59), font=font_body)
        draw.text((44, 302), status_text[:45], fill=(37, 99, 235) if anim_type != "initial" else (16, 185, 129), font=font_small)

        # Buttons
        buttons = ["Перемещение (Translate)", "Вращение (Rotate)", "Масштаб (Scale)"]
        btn_y = 356
        for i, b_text in enumerate(buttons):
            is_active = (
                (i == 0 and anim_type == "translate") or
                (i == 1 and anim_type == "rotate") or
                (i == 2 and anim_type == "scale")
            )
            b_bg = (37, 99, 235) if is_active else (241, 245, 249)
            b_fg = (255, 255, 255) if is_active else (71, 85, 105)
            draw.rounded_rectangle([(24, btn_y), (width - 24, btn_y + 40)], radius=8, fill=b_bg)
            draw.text((width // 2 - len(b_text) * 3 - 6, btn_y + 12), b_text, fill=b_fg, font=font_body)
            btn_y += 50

        if toast_text:
            draw.rounded_rectangle([(40, 530), (width - 40, 568)], radius=18, fill=(30, 41, 59))
            draw.text((width // 2 - len(toast_text) * 3 - 4, 542), toast_text, fill=(255, 255, 255), font=font_small)

        output_image_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(output_image_path))
        return output_image_path

    def render_database_screen(
        self,
        step_name: str,
        output_image_path: Path,
        step_index: int = 1
    ) -> Path:
        width, height = 400, 680
        img = Image.new("RGB", (width, height), (248, 250, 252))
        draw = ImageDraw.Draw(img)

        font_body = self._get_font(13, mono=False)
        font_small = self._get_font(11, mono=False)
        font_bold = self._get_font(13, mono=False, bold=True)

        self._draw_android_frame(draw, width, height, step_index, "База данных SQLite")

        # Search bar
        draw.rounded_rectangle([(24, 96), (width - 24, 134)], radius=8, fill=(255, 255, 255), outline=(203, 213, 225), width=1)
        draw.text((36, 107), "🔍 Поиск по записям...", fill=(148, 163, 184), font=font_small)

        # Records List
        records = [
            ("Кашевич Е.Н.", "Группа ПМ-31 • Отл.", "ID: 101"),
            ("Иванов И.И.", "Группа ПМ-31 • Хор.", "ID: 102"),
            ("Петров П.П.", "Группа ПМ-31 • Зачет", "ID: 103"),
            ("Сидоров С.С.", "Группа ПМ-31 • Отл.", "ID: 104")
        ]

        if step_name in ["add", "filled"]:
            # Form dialog overlay
            draw.rounded_rectangle([(24, 150), (width - 24, 460)], radius=12, fill=(255, 255, 255), outline=(37, 99, 235), width=2)
            draw.text((44, 170), "Добавление новой записи в БД", fill=(15, 23, 42), font=font_bold)

            fields = [("ФИО студента", "Кашевич Е.Н."), ("Учебная группа", "ПМ-31"), ("Успеваемость", "9 (отлично)")]
            fy = 205
            for lbl, val in fields:
                draw.text((44, fy), lbl, fill=(100, 116, 139), font=font_small)
                draw.rounded_rectangle([(44, fy + 16), (width - 44, fy + 48)], radius=6, fill=(248, 250, 252), outline=(203, 213, 225), width=1)
                draw.text((54, fy + 23), val if step_name == "filled" else "", fill=(15, 23, 42), font=font_body)
                fy += 58

            draw.rounded_rectangle([(44, 395), (width - 44, 435)], radius=6, fill=(37, 99, 235))
            draw.text((width // 2 - 45, 406), "Вставить в SQLite", fill=(255, 255, 255), font=font_body)
        else:
            ry = 146
            for idx, (name, grp, rec_id) in enumerate(records):
                is_new = (idx == 0 and step_name == "result")
                border_c = (16, 185, 129) if is_new else (226, 232, 240)
                bg_c = (240, 253, 244) if is_new else (255, 255, 255)
                draw.rounded_rectangle([(24, ry), (width - 24, ry + 64)], radius=8, fill=bg_c, outline=border_c, width=2 if is_new else 1)
                draw.text((40, ry + 12), name, fill=(15, 23, 42), font=font_bold)
                draw.text((40, ry + 36), grp, fill=(100, 116, 139), font=font_small)
                draw.text((width - 85, ry + 24), rec_id, fill=(37, 99, 235), font=font_small)
                ry += 74

            # Floating Action Button (+)
            draw.ellipse([(width - 76, height - 120), (width - 26, height - 70)], fill=(37, 99, 235))
            draw.text((width - 56, height - 108), "+", fill=(255, 255, 255), font=font_bold)

        output_image_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(output_image_path))
        return output_image_path

    def render_general_mobile_screen(
        self,
        title: str,
        topic: str,
        fig_title: str,
        output_image_path: Path,
        step_index: int = 1
    ) -> Path:
        width, height = 400, 680
        img = Image.new("RGB", (width, height), (248, 250, 252))
        draw = ImageDraw.Draw(img)

        font_body = self._get_font(13, mono=False)
        font_small = self._get_font(11, mono=False)
        font_bold = self._get_font(13, mono=False, bold=True)

        app_title = topic[:25] if topic else "Мобильное приложение"
        self._draw_android_frame(draw, width, height, step_index, app_title)

        # Card
        draw.rounded_rectangle([(24, 108), (width - 24, 440)], radius=12, fill=(255, 255, 255), outline=(226, 232, 240), width=1)

        # Header in card
        screen_heading = fig_title if fig_title else f"Экран программы {step_index}"
        draw.text((40, 128), screen_heading[:36], fill=(15, 23, 42), font=font_bold)
        draw.text((40, 154), f"Шаг выполнения #{step_index} • Режим работы", fill=(100, 116, 139), font=font_small)

        # Form / Info items
        items = [
            ("Пользователь", "Кашевич Е.Н."),
            ("Учебная группа", "ПМ-31"),
            ("Текущий статус", "Выполнено успешно"),
            ("Параметр потока", f"Thread-ID: #00{step_index}")
        ]
        iy = 190
        for lbl, val in items:
            draw.text((40, iy), lbl, fill=(100, 116, 139), font=font_small)
            draw.rounded_rectangle([(40, iy + 18), (width - 40, iy + 52)], radius=6, fill=(248, 250, 252), outline=(226, 232, 240), width=1)
            draw.text((50, iy + 26), val, fill=(15, 23, 42), font=font_body)
            iy += 62

        # Action Buttons
        draw.rounded_rectangle([(24, 460), (width - 24, 504)], radius=8, fill=(37, 99, 235))
        draw.text((width // 2 - 50, 473), "Выполнить операцию", fill=(255, 255, 255), font=font_body)

        draw.rounded_rectangle([(24, 514), (width - 24, 558)], radius=8, fill=(241, 245, 249))
        draw.text((width // 2 - 45, 527), "Сброс параметров", fill=(71, 85, 105), font=font_body)

        output_image_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(output_image_path))
        return output_image_path

    def render_ui_wireframe(
        self,
        title: str,
        topic: str,
        output_image_path: Path,
        step_index: int = 1,
        fig_title: str = ""
    ) -> Path:
        width, height = 900, 560
        img = Image.new("RGB", (width, height), (248, 250, 252))
        draw = ImageDraw.Draw(img)

        font_header = self._get_font(15, mono=False, bold=True)
        font_body = self._get_font(13, mono=False)
        font_small = self._get_font(11, mono=False)

        # 1. Figma / Browser Frame Bar
        draw.rectangle([(0, 0), (width, 44)], fill=(226, 232, 240))
        draw.ellipse([(16, 16), (28, 28)], fill=(239, 68, 68))
        draw.ellipse([(36, 16), (48, 28)], fill=(245, 158, 11))
        draw.ellipse([(56, 16), (68, 28)], fill=(16, 185, 129))
        draw.rounded_rectangle([(100, 10), (width - 120, 34)], radius=6, fill=(255, 255, 255))
        display_title = fig_title if fig_title else topic
        draw.text((120, 14), f"Figma / Web Prototype — {display_title[:50]}", fill=(100, 116, 139), font=font_small)

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
        draw.text((40, 125), display_title[:55] if display_title else "Разработка структуры пользовательского интерфейса", fill=(15, 23, 42), font=font_header)
        draw.text((40, 155), f"Макет №{step_index}: адаптивная сетка (12-column grid), auto-layout и дизайн-система", fill=(100, 116, 139), font=font_small)
        draw.rounded_rectangle([(40, 195), (180, 230)], radius=6, fill=(37, 99, 235))
        draw.text((65, 205), "Подробнее", fill=(255, 255, 255), font=font_body)
        draw.rounded_rectangle([(width - 320, 120), (width - 40, 245)], radius=10, fill=(255, 255, 255), outline=(203, 213, 225), width=2)
        draw.text((width - 240, 175), f"UI Frame {step_index}", fill=(148, 163, 184), font=font_small)

        # 4. Content Cards Grid
        card_w = (width - 80 - 40) // 3
        for i in range(3):
            cx = 40 + i * (card_w + 20)
            cy = 280
            draw.rounded_rectangle([(cx, cy), (cx + card_w, cy + 160)], radius=8, fill=(255, 255, 255), outline=(226, 232, 240), width=1)
            draw.rounded_rectangle([(cx + 10, cy + 10), (cx + card_w - 10, cy + 80)], radius=6, fill=(241, 245, 249))
            draw.text((cx + card_w//2 - 35, cy + 40), f"Модуль {i+1}", fill=(100, 116, 139), font=font_small)
            draw.text((cx + 15, cy + 95), f"Элемент экрана {step_index}.{i+1}", fill=(30, 41, 59), font=font_body)
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
        output_image_path: Path,
        state: str = "initial",
        fig_title: str = "",
        step_index: int = 1
    ) -> Path:
        """Intelligently detects the topic domain and renders matching, realistic screenshots."""
        context = (subject + " " + topic + " " + fig_title + " " + state + " " + code).lower()

        # 1. Design / Figma / UI/UX
        is_design = any(w in context for w in ["дизайн", "design", "figma", "макет", "ui/ux"]) and not (code.strip() and "import" in code)
        if is_design:
            return self.render_ui_wireframe(
                title=subject or "UI/UX Design Mockup",
                topic=topic or "Разработка интерфейса пользователя",
                output_image_path=output_image_path,
                step_index=step_index,
                fig_title=fig_title
            )

        # 2. Mobile App Check
        is_mobile = any(w in context for w in [
            "мобил", "android", "androidx", "import android", "setcontentview", "activity", "strings.xml"
        ])

        if is_mobile:
            # Check domain: Localization
            is_loc = any(w in context for w in ["локализ", "strings.xml", "values-ru", "values-be", "values-en", "locale", "язык", "белорус", "русск", "английск"])
            if is_loc:
                loc_check = (fig_title + " " + state).lower()
                if "белорус" in loc_check or "be" in loc_check or (step_index == 2 and "результат" not in loc_check):
                    lang = "be"
                elif "англ" in loc_check or "en" in loc_check or (step_index == 3 and "результат" not in loc_check):
                    lang = "en"
                elif "результат" in loc_check or "сохранен" in loc_check or step_index == 4:
                    lang = "res"
                else:
                    lang = "ru"
                return self.render_localization_screen(lang, output_image_path, step_index)

            # Check domain: Animation
            is_anim = any(w in context for w in ["анимац", "translate", "rotate", "scale", "alpha"])
            if is_anim:
                anim_check = (fig_title + " " + state).lower()
                if "translate" in anim_check or "перемещ" in anim_check:
                    a_type = "translate"
                elif "rotate" in anim_check or "вращ" in anim_check:
                    a_type = "rotate"
                elif "scale" in anim_check or "масштаб" in anim_check:
                    a_type = "scale"
                else:
                    a_type = "initial"
                return self.render_animation_screen(a_type, output_image_path, step_index)

            # Check domain: Database / SQLite / ListView
            is_db = any(w in context for w in ["баз", "sqlite", "db", "listview", "recyclerview", "запис", "cursor"])
            if is_db:
                db_check = (fig_title + " " + state).lower()
                if "добав" in db_check or "ввод" in db_check or step_index == 2:
                    s_name = "add"
                elif "заполн" in db_check or step_index == 3:
                    s_name = "filled"
                elif "результат" in db_check or step_index == 4:
                    s_name = "result"
                else:
                    s_name = "list"
                return self.render_database_screen(s_name, output_image_path, step_index)

            # General Mobile Screen (Adaptive to fig_title)
            return self.render_general_mobile_screen(
                title=subject or "Android App",
                topic=topic or "Мобильное приложение",
                fig_title=fig_title,
                output_image_path=output_image_path,
                step_index=step_index
            )

        # 3. Console / Algorithm / Terminal
        term_title = f"Terminal — Тест #{step_index}: {fig_title[:35]}" if fig_title else "Terminal — mugo@arch: ~/labs"
        return self.render_terminal(
            command=command,
            output_text=output_text,
            output_image_path=output_image_path,
            title=term_title
        )

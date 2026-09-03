import argparse
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from autolab.config import load_config, save_config
from autolab.pipeline import LabPipeline

console = Console()

def main():
    parser = argparse.ArgumentParser(description="AutoLab AI — Автоматическая генерация лабораторных работ по Белорусскому ГОСТу")
    parser.add_argument("--task", type=str, help="Текст задания или формулировка темы")
    parser.add_argument("--subject", type=str, default="", help="Учебный предмет (например: СУБД, Разработка ПО, ТРПО)")
    parser.add_argument("--variant", type=str, default="", help="Номер варианта")
    parser.add_argument("--date", type=str, default="", help="Дата выполнения работы (например: 24.03.2026)")
    parser.add_argument("--theory", action="store_true", help="Добавить теоретические сведения (по умолчанию выключено)")
    parser.add_argument("--file", type=str, help="Путь к файлу методички (PDF, DOCX или изображение)")
    parser.add_argument("--title-page", action="store_true", help="Сгенерировать титульный лист")
    parser.add_argument("--set-key", type=str, help="Сохранить бесплатный ключ Gemini API")
    parser.add_argument("--info", action="store_true", help="Показать текущие настройки профиля студента")
    parser.add_argument("-i", "--interactive", action="store_true", help="Интерактивный пошаговый режим")

    args = parser.parse_args()
    config = load_config()

    if args.set_key:
        config.gemini_api_key = args.set_key.strip()
        save_config(config)
        console.print("[bold green]✓ Ключ Gemini API успешно сохранен![/bold green]")
        return

    if args.info:
        table = Table(title="Настройки профиля студента (ГОСТ)")
        table.add_column("Параметр", style="cyan")
        table.add_column("Значение", style="magenta")
        table.add_row("Учреждение", config.student.institution)
        table.add_row("Специальность", config.student.specialty)
        table.add_row("Группа", config.student.group)
        table.add_row("Обучающийся", config.student.student_name)
        table.add_row("Преподаватель", config.student.teacher_name)
        table.add_row("Модель Gemini", config.model_name)
        table.add_row("API Ключ", "Установлен" if config.gemini_api_key else "НЕ установлен (Демо-режим)")
        console.print(table)
        return

    task_text = args.task or ""
    subject = args.subject or ""
    variant = args.variant or ""
    file_path = Path(args.file) if args.file else None
    with_title = args.title_page

    if args.interactive and not task_text and not file_path:
        console.print(Panel("[bold cyan]AutoLab AI — Мастер генерации лабораторной работы[/bold cyan]"))
        subject = console.input("[yellow]Введите название предмета (Enter для авто): [/yellow]").strip()
        variant = console.input("[yellow]Введите номер варианта (Enter если нет): [/yellow]").strip()
        f_input = console.input("[yellow]Путь к файлу методички (PDF/DOCX/фото) или Enter: [/yellow]").strip()
        if f_input:
            file_path = Path(f_input)
        task_text = console.input("[yellow]Текст задания или краткое описание: [/yellow]").strip()
        tp_input = console.input("[yellow]Добавить титульный лист? (д/н, по умолч. н): [/yellow]").strip().lower()
        with_title = tp_input in ["д", "y", "да", "yes"]

    if not task_text and not file_path:
        console.print("[red]Ошибка: Укажите текст задания (--task), файл методички (--file) или используйте флаг -i для интерактивного ввода.[/red]")
        sys.exit(1)

    pipeline = LabPipeline(config)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("[cyan]Генерация лабораторной работы...", total=None)
        try:
            result = pipeline.run(
                task_text=task_text,
                subject=subject,
                variant=variant,
                date_str=args.date,
                include_theory=args.theory,
                uploaded_file=file_path,
                with_title_page=with_title
            )
        except Exception as e:
            console.print(f"[bold red]Ошибка генерации: {e}[/bold red]")
            sys.exit(1)

    console.print("\n[bold green]✓ Лабораторная работа успешно создана![/bold green]")
    console.print(f"[bold cyan]Файл отчета (.docx):[/bold cyan] [underline]{result['docx_path']}[/underline]")
    console.print(f"[bold cyan]Снимок экрана:[/bold cyan] [underline]{result['screenshot_path']}[/underline]")
    
    sol = result["solution"]
    console.print(Panel(
        f"[bold]Тема:[/bold] {sol.get('topic')}\n"
        f"[bold]Цель:[/bold] {sol.get('goal')}\n"
        f"[bold]Код:[/bold] {sol.get('code_language')} ({len(sol.get('code', ''))} символов)\n"
        f"[bold]Вывод:[/bold] {sol.get('conclusion')}",
        title="Информация о выполненной работе"
    ))

if __name__ == "__main__":
    main()

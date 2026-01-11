import os
from pathlib import Path

# Шаблонные настройки — Qwen позже заменит на конфигурируемые
DEFAULT_EXCLUDE_PATTERNS = {
    "__pycache__", ".git", "venv", ".idea", ".vscode",
    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.log"
}

def should_exclude(path: Path, root: Path) -> bool:
    """Проверяет, нужно ли исключить файл/папку."""
    rel_parts = path.relative_to(root).parts
    name = path.name
    suffix = path.suffix.lower()

    # Исключить по имени папки/файла
    if any(part in DEFAULT_EXCLUDE_PATTERNS for part in rel_parts):
        return True

    # Исключить по расширению
    if f"*{suffix}" in DEFAULT_EXCLUDE_PATTERNS:
        return True

    return False

def simulate_backup(project_path: str, target_format: str) -> str:
    """
    Заглушка: имитирует бэкап.
    Позже Qwen заменит на реальную логику копирования и переименования.
    """
    project = Path(project_path)
    if not project.exists():
        return f"❌ Проект не найден: {project_path}"

    # Просто подсчитаем .py файлы (для демо)
    py_files = [
        f for f in project.rglob("*.py")
        if not should_exclude(f, project)
    ]

    return (
        f"✅ Готово!\n"
        f"Проект: {project_path}\n"
        f"Формат: {target_format}\n"
        f"Найдено .py файлов: {len(py_files)}\n"
        f"Результат будет в папке: for{target_format.capitalize()}"
    )
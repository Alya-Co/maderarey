"""
list_empty.py

Показывает все папки houses/*, у которых 0 фото в data.json — это, скорее
всего, письма-переписка без вложений (ответы, пересылки без файлов).
Ничего не удаляет — только показывает список для ручной проверки.

Запускать из корня репозитория:
    python list_empty.py
"""

import json
from pathlib import Path

HOUSES_DIR = Path("houses_v2")

def main():
    if not HOUSES_DIR.exists():
        print(f"Папка {HOUSES_DIR} не найдена. Запусти скрипт оттуда, где она лежит рядом.")
        return

    empty = []
    total = 0
    for path in sorted(HOUSES_DIR.glob("*/data.json")):
        total += 1
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            empty.append((path.parent.name, "битый data.json"))
            continue
        photos = data.get("photos", [])
        if not photos:
            price = data.get("price", 0)
            name = data.get("name", "")
            empty.append((path.parent.name, f"name={name!r} price={price}"))

    print(f"Всего папок: {total}")
    print(f"Папок без фото: {len(empty)}\n")
    for slug, info in empty:
        print(f"  {slug:35} {info}")

    print(f"\nЕсли удалить эти {len(empty)} папок, останется: {total - len(empty)}")

if __name__ == "__main__":
    main()

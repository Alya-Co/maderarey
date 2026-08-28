"""
set_featured.py

Помечает, какие дома показывать в карусели скидок на главной странице.
Просто впиши нужные слаги (имена папок) в список FEATURED_SLUGS ниже и
запусти скрипт — он проставит "featured": true этим домам и уберёт
пометку у всех остальных.

После запуска не забудь прогнать generate_catalog.py, чтобы карусель
на сайте обновилась.

Запускать из корня репозитория:
    python set_featured.py
"""

import json
from pathlib import Path

HOUSES_DIR = Path("houses")

# ── Впиши сюда слаги (имена папок) домов, которые хочешь рекламировать ──
FEATURED_SLUGS = [
    "oskar-68-8.87x10.04",
    "leon-58-9.4x10.7",
    # "verona-68-5.93x8.75",
    # "wendy-68-9.7x9.8",
]
# ──────────────────────────────────────────────────────────────────────


def main():
    if not HOUSES_DIR.exists():
        print("Папка houses/ не найдена. Запусти скрипт из корня репозитория.")
        return

    featured_set = set(FEATURED_SLUGS)
    found = set()
    changed = 0

    for path in sorted(HOUSES_DIR.glob("*/data.json")):
        slug = path.parent.name
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"  [пропуск] {slug}: битый data.json ({e})")
            continue

        should_be_featured = slug in featured_set
        currently_featured = bool(data.get("featured"))

        if should_be_featured:
            found.add(slug)

        if should_be_featured and not currently_featured:
            data["featured"] = True
            changed += 1
        elif not should_be_featured and currently_featured:
            data.pop("featured", None)
            changed += 1
        else:
            continue

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    missing = featured_set - found
    if missing:
        print(f"[!] Не найдены папки для слагов: {', '.join(missing)} — проверь написание")

    print(f"Обновлено файлов: {changed}")
    print(f"Сейчас помечены как featured: {', '.join(sorted(found)) or '(никто)'}")
    print("\nТеперь запусти: python generate_catalog.py")


if __name__ == "__main__":
    main()

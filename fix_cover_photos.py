"""
fix_cover_photos.py

Многие дома показывают на карточке в каталоге план этажа вместо фото дома —
потому что план случайно оказался первым в списке "photos". Этот скрипт
сам переставляет фото каждого дома так, чтобы первым (обложкой) шёл не
план, а нормальный рендер/фото дома. Порядок остальных фото не меняется.

Определяет "план" и "рендер" по ключевым словам в имени файла — судя по
всем письмам Виктора, разметка достаточно стабильная:
  план/чертёж:  fp, distr, dimen, plan, planta
  рендер/фото:  3d, exter, ext, mueble, aspecto

Ничего не удаляет, только меняет порядок в поле "photos" в data.json.

Запускать из корня репозитория:
    python fix_cover_photos.py
"""

import json
import re
from pathlib import Path

HOUSES_DIR = Path("houses")

PLAN_KEYWORDS = ["fp", "distr", "dimen", "planta", "_plan"]
RENDER_KEYWORDS = ["3d", "exter", "_ext", "mueble", "aspecto"]


def photo_score(filename):
    """Больше = лучше подходит на обложку. Отрицательный = похоже на план."""
    name = filename.lower()
    score = 0
    if any(kw in name for kw in PLAN_KEYWORDS):
        score -= 10
    if any(kw in name for kw in RENDER_KEYWORDS):
        score += 5
    return score


def main():
    if not HOUSES_DIR.exists():
        print("Папка houses/ не найдена. Запусти скрипт из корня репозитория.")
        return

    changed = 0
    unchanged = 0
    no_good_photo = []

    for path in sorted(HOUSES_DIR.glob("*/data.json")):
        slug = path.parent.name
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"  [пропуск] {slug}: битый data.json ({e})")
            continue

        photos = data.get("photos", [])
        if len(photos) < 2:
            unchanged += 1
            continue

        current_first_score = photo_score(photos[0])
        best_score = max(photo_score(p) for p in photos)

        if current_first_score >= best_score:
            # первое фото уже не хуже остальных — не трогаем
            unchanged += 1
            continue

        if best_score < 0:
            # вообще ни одно фото не похоже на нормальный рендер
            no_good_photo.append(slug)

        # сортируем по убыванию "качества обложки", стабильно (сохраняя
        # взаимный порядок при равном счёте)
        new_order = sorted(photos, key=lambda p: -photo_score(p))
        if new_order != photos:
            print(f"  {slug}: '{photos[0]}' → '{new_order[0]}'")
            data["photos"] = new_order
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            changed += 1
        else:
            unchanged += 1

    print(f"\nПоменяли обложку: {changed}")
    print(f"Без изменений: {unchanged}")
    if no_good_photo:
        print(f"\n[!] У этих домов вообще нет фото, непохожего на план "
              f"(проверь вручную): {', '.join(no_good_photo)}")
    print("\nТеперь запусти: python generate_catalog.py")


if __name__ == "__main__":
    main()

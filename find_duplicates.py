"""
find_duplicates.py

Ищет вероятные дубли среди houses/*/ — сравнивает данные (название, цена,
размер, площадь, количество/имена фото) и предлагает список пар-кандидатов
на дубль. НИЧЕГО не удаляет — только печатает отчёт, решение о том, какую
папку оставить, а какую убрать, принимаешь сама.

Запускать из корня репозитория:
    python find_duplicates.py
"""

import json
import re
from pathlib import Path
from difflib import SequenceMatcher

HOUSES_DIR = Path("houses")


def normalize(text):
    """Убирает пробелы, дефисы, диакритику, приводит к нижнему регистру —
    чтобы 'Ibérica-T3' и 'iberica-t3' совпали при сравнении."""
    text = text.lower()
    text = (text.replace("é", "e").replace("á", "a").replace("í", "i")
                .replace("ó", "o").replace("ú", "u").replace("ñ", "n"))
    text = re.sub(r"[-_\s]+", "", text)
    return text


def name_similarity(a, b):
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def load_houses():
    houses = []
    for path in sorted(HOUSES_DIR.glob("*/data.json")):
        slug = path.parent.name
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print(f"  [!] {slug}: битый data.json, пропускаю")
            continue
        houses.append((slug, data))
    return houses


def compare(slug_a, data_a, slug_b, data_b):
    """Возвращает (score, reasons, verdict) — насколько похожи два дома."""
    reasons = []
    score = 0

    # Похожесть названия папки/слага
    sim = name_similarity(slug_a, slug_b)
    if sim > 0.75:
        score += 2
        reasons.append(f"похожие имена папок ({sim:.0%})")

    # Похожесть названия дома внутри data.json
    name_a, name_b = data_a.get("name", ""), data_b.get("name", "")
    if name_a and name_b:
        nsim = name_similarity(name_a, name_b)
        if nsim > 0.8:
            score += 2
            reasons.append(f"похожие названия дома ('{name_a}' vs '{name_b}')")

    # Толщина стены — КЛЮЧЕВОЙ индикатор. Разная толщина при том же размере
    # почти всегда значит РАЗНЫЕ товары (подтверждено клиентом), а не дубль.
    thick_a = str(data_a.get("thickness", "")).strip()
    thick_b = str(data_b.get("thickness", "")).strip()
    thickness_conflict = False
    if thick_a and thick_b:
        if thick_a == thick_b:
            score += 2
            reasons.append(f"одинаковая толщина стены ({thick_a})")
        else:
            thickness_conflict = True
            reasons.append(f"⚠ РАЗНАЯ толщина стены ({thick_a} vs {thick_b}) — вероятно разные товары")

    # Совпадение цены — считаем только реальные ненулевые цены, иначе
    # "0 == 0" на двух домах с непропарсенной ценой давало ложные совпадения
    price_a, price_b = data_a.get("price"), data_b.get("price")
    if price_a and price_b and price_a == price_b:
        score += 3
        reasons.append(f"одинаковая цена ({price_a})")

    # Совпадение размера
    size_a, size_b = data_a.get("size", ""), data_b.get("size", "")
    if size_a and size_a == size_b:
        score += 1
        reasons.append(f"одинаковый размер ({size_a})")

    # Совпадение количества фото и похожие имена файлов фото
    photos_a = set(data_a.get("photos", []))
    photos_b = set(data_b.get("photos", []))
    if photos_a and photos_b:
        overlap = len(photos_a & photos_b)
        if overlap > 0:
            score += 3
            reasons.append(f"{overlap} одинаковых файлов фото")
        elif len(photos_a) == len(photos_b):
            score += 1
            reasons.append(f"одинаковое число фото ({len(photos_a)})")

    # Если толщина явно разная — это почти наверняка НЕ дубль, даже при
    # высоком score по другим признакам. Понижаем и помечаем.
    verdict = "дубль?"
    if thickness_conflict:
        score = max(score - 5, 0)
        verdict = "разные товары (толщина отличается)"

    return score, reasons, verdict


def main():
    if not HOUSES_DIR.exists():
        print("Папка houses/ не найдена. Запусти скрипт из корня репозитория.")
        return

    houses = load_houses()
    print(f"Загружено домов: {len(houses)}\n")

    candidates = []
    for i in range(len(houses)):
        for j in range(i + 1, len(houses)):
            slug_a, data_a = houses[i]
            slug_b, data_b = houses[j]
            score, reasons, verdict = compare(slug_a, data_a, slug_b, data_b)
            if score >= 4:
                candidates.append((score, slug_a, slug_b, reasons, verdict))

    candidates.sort(key=lambda c: -c[0])

    if not candidates:
        print("Явных дублей не найдено.")
        return

    real_dupes = [c for c in candidates if c[4] == "дубль?"]
    different = [c for c in candidates if c[4] != "дубль?"]

    print(f"=== ВЕРОЯТНЫЕ ДУБЛИ (нужно решить: оставить одну папку) — {len(real_dupes)} ===\n")
    for score, slug_a, slug_b, reasons, verdict in real_dupes:
        print(f"[score={score}] {slug_a}  <->  {slug_b}")
        for r in reasons:
            print(f"    - {r}")
        print()

    if different:
        print(f"\n=== ПОХОЖИ, НО ПОХОЖЕ РАЗНЫЕ ТОВАРЫ (можно не трогать) — {len(different)} ===\n")
        for score, slug_a, slug_b, reasons, verdict in different:
            print(f"[score={score}] {slug_a}  <->  {slug_b}  — {verdict}")
            for r in reasons:
                print(f"    - {r}")
            print()


if __name__ == "__main__":
    main()

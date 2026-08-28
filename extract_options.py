"""
extract_options.py

Проходит по всем houses/*/data.json, находит в description строки вида
"... - 4300" (цены-коды опций из писем Виктора), раскладывает их по полю
options (ins_roof / ins_wall / tegola) и убирает эти строки из description,
оставляя только человеческий текст.

Запускать из корня репозитория (там же, где папка houses/):
    python extract_options.py

Ничего не удаляет безвозвратно необратимо — просто переписывает data.json.
Сначала можно прогнать с DRY_RUN = True, чтобы посмотреть, что найдёт,
не трогая файлы.
"""

import json
import re
from pathlib import Path

HOUSES_DIR = Path("houses")
DRY_RUN = False  # поставь True, чтобы сначала посмотреть, ничего не меняя

# Строка похожа на "текст ... - 4300" или "... - 4300 eur" (число в конце
# после тире, необязательно с "eur"/"€")
PRICE_LINE_RE = re.compile(r"^(?P<label>.+?)\s*-\s*(?P<price>\d+)\s*(?:eur|€)?\.?\s*$", re.IGNORECASE)

# По каким словам в строке определяем, какая это опция
KEYWORD_MAP = {
    "ins_roof": ["tejado", "techo"],
    "ins_wall": ["pared", "paredes"],
    "tegola":   ["tegola", "teja"],
}


def classify(label: str):
    """Возвращает ключ опции (ins_roof/ins_wall/tegola) по тексту строки, либо None."""
    label_low = label.lower()
    for key, words in KEYWORD_MAP.items():
        if any(w in label_low for w in words):
            return key
    return None


def process_file(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    description = data.get("description", "")
    lines = description.split("\n")

    kept_lines = []
    found_options = {}

    for line in lines:
        stripped = line.strip()
        m = PRICE_LINE_RE.match(stripped)
        if m:
            price = int(m.group("price"))
            label = m.group("label")
            key = classify(label)
            if key:
                found_options[key] = price
                continue  # убираем строку из описания
        kept_lines.append(line)

    if not found_options:
        print(f"  [пропуск] {path.parent.name}: цены опций в описании не найдены")
        return

    new_description = "\n".join(kept_lines).strip()

    print(f"  [{path.parent.name}] найдено: {found_options}")

    if DRY_RUN:
        return

    data["description"] = new_description
    # не затираем уже существующие значения, если они там были проставлены руками
    existing = data.get("options", {})
    existing.update({k: v for k, v in found_options.items() if k not in existing})
    data["options"] = existing

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    if not HOUSES_DIR.exists():
        print("Папка houses/ не найдена. Запусти скрипт из корня репозитория.")
        return

    data_files = sorted(HOUSES_DIR.glob("*/data.json"))
    print(f"Найдено файлов data.json: {len(data_files)}")
    if DRY_RUN:
        print("=== DRY RUN — файлы не изменяются ===")

    for path in data_files:
        process_file(path)

    print("Готово.")


if __name__ == "__main__":
    main()

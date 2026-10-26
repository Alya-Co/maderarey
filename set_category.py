"""
set_category.py

Раскладывает дома по вкладкам каталога (Cabañas, Casetas —
Garajes и Premium определяются автоматически: Garajes по названию
("garaje"/"cochera"), Premium по метке premium_marker в data.json,
которую download_houses.py ставит, если в теме письма Виктора
буквально было слово "Premium" — толщина стены на это НЕ влияет.
Viviendas — категория по умолчанию для всех, кого не перечислили
ниже явно).

Дом может быть сразу в НЕСКОЛЬКИХ вкладках одновременно — например,
гараж с меткой Premium должен быть виден и в Garajes, и в Premium.
Поэтому списки ниже ДОБАВЛЯЮТ категорию поверх автоопределения, а не
заменяют её: если слаг гаража вписан в PREMIUM, он всё равно останется
в Garajes (это определяется автоматически по названию) и вдобавок
появится в Premium.

Впиши слаги (имена папок) в нужные списки и запусти скрипт.
Один и тот же слаг можно вписать сразу в несколько списков.

После запуска прогони generate_catalog.py, чтобы сайт обновился.

Запускать из корня репозитория:
    python set_category.py
"""

import json
from pathlib import Path

HOUSES_DIR = Path("houses")

# ── Впиши сюда слаги домов по категориям ────────────────────────────────
CABANAS = [
    # Уточнено у Виктора 01.10.2026 (WhatsApp)
    "oficina-bergen-44-4.2x8",
    "oficina-emily-44-4.04x7.8",
    "ottawa-44-6x4.5",
    # Отмечено клиентом в MaderaRey_categorias (28.08.2026)
    "eko-44-5x5.7",
    "hakan-a-44-6x5.2",
    "helmand-44-3x9",
    "linus-44-4x4",
    "linus-44-4x5",
    "linus-44-5x4",
    "linus-44-5x4-wc",
    "linus-44-5x5",
    "linus-44-5x5-wc",
    "linus-44-6x4",
    "linus-44-6x5",
    "linus-44-6x5-wc",
    "linus-44-6x6",
    "linus-44-6x6-wc",
    "louise-44-6x6",
    "murray-44-4x6",
    "padova-a-44-6x4.5",
    "rico-44-4.04x7.8",
    "roberto-44-5.6x4",
    "trento-44-6x5",
]

CASETAS = [
    # Уточнено у Виктора 01.10.2026 (WhatsApp)
    "oficina-nuuk-44-5x3.84",
    "oficina-wik-44-4.5x3.5",
    # Отмечено клиентом в MaderaRey_categorias (28.08.2026)
    "deko-44-5x3",
    "erna-44-2.5x4.5",
    "milano-44-3.8x5.3",
]

PREMIUM = [
    # ФИНАЛЬНЫЙ список Premium — прислал Виктор в WhatsApp 01.10.2026
    # («Категория premium: Torino, Alma, Louise, Lukas, Almería, Gustav A 6x6,
    # Gustav A wc 6x6, Orlando, Gustav B 6x8, Gustav B wc 6x8, Scarlett,
    # Jennifer, Ibérica T3, Sevilla»). Всё остальное с пометкой Premium в
    # письмах (Linus, Murray, гаражи и т.д.) во вкладку Premium НЕ входит.
    "torino-44-4.5x6",               # Torino
    "alma-44-7.05x8",                # Alma
    "louise-44-6x6",                 # Louise
    "lukas-44-6.5x7.7",              # Lukas
    "almería-44-6x8.87",             # Almería
    "gustav-a-44-6x6",               # Gustav A 6x6
    "gustav-a-44-6x6-wc",            # Gustav A wc 6x6
    "orlando-44-8x9",                # Orlando
    "gustav-b-44-6x8",               # Gustav B 6x8
    "gustav-b-44-6x8-wc",            # Gustav B wc 6x8
    "scarlett-44-7x10.2",            # Scarlett
    "jennifer-44-10.5x8.52",         # Jennifer
    "ibérica-t3-44-7.92x11.84",      # Ibérica T3
    "sevilla-44-7.8x13.74",          # Sevilla
]
# ─────────────────────────────────────────────────────────────────────

# слаг → set() категорий, которые нужно ДОБАВИТЬ (один слаг может быть
# сразу в нескольких списках выше)
DESIRED = {}
for slug in CABANAS:
    DESIRED.setdefault(slug, set()).add("cabanas")
for slug in CASETAS:
    DESIRED.setdefault(slug, set()).add("casetas")
for slug in PREMIUM:
    DESIRED.setdefault(slug, set()).add("premium")


def main():
    if not HOUSES_DIR.exists():
        print("Папка houses/ не найдена. Запусти скрипт из корня репозитория.")
        return

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

        target = DESIRED.get(slug)  # None/пусто = не менять (авто/vivienda)
        if slug in DESIRED:
            found.add(slug)

        current_raw = data.get("category")
        if current_raw is None:
            current = set()
        elif isinstance(current_raw, str):
            current = {current_raw}
        else:
            current = set(current_raw)

        if target:
            new_value = sorted(target)
            if current != target:
                data["category"] = new_value if len(new_value) > 1 else new_value[0]
                changed += 1
            else:
                continue
        elif current:
            # раньше была вручную назначена категория, а теперь слаг убрали
            # из списков выше — возвращаем к чистому автоопределению
            data.pop("category", None)
            changed += 1
        else:
            continue

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    missing = set(DESIRED) - found
    if missing:
        print(f"[!] Не найдены папки для слагов: {', '.join(sorted(missing))} — проверь написание")

    print(f"Обновлено файлов: {changed}")
    print("\nТеперь запусти: python generate_catalog.py")


if __name__ == "__main__":
    main()

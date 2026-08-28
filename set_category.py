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
    # Отмечено клиентом в MaderaRey_categorias (28.08.2026)
    "deko-44-5x3",
    "erna-44-2.5x4.5",
    "milano-44-3.8x5.3",
]

PREMIUM = [
    # Составлено по темам писем Виктора со скриншотов Gmail (28-29 июля).
    # Слаги — это МОЯ реконструкция по правилам parse_subject()/
    # make_folder_name(), а не прямое чтение папок houses/ (их у меня
    # нет в этой сессии). Если слаг не совпадёт с реальным именем папки —
    # ничего не сломается, скрипт просто выведет предупреждение
    # "не найдены папки для слагов" и пропустит его.
    "oficina-bergen-44-4.2x8",        # oficina 44 Bergen 4,2x8-Premium - 8000
    "oficina-nuuk-44-5x3.84",         # oficina 44 Nuuk 5x3,84-Premium - 5000
    "oficina-wik-44-4.5x3.5",         # oficina 44 Wik 4,5x3,5-Premium - 5300
    "oficina-emily-44-4.04x7.8",      # oficina 44 Emily 4,04x7,8-Premium - 7600
    "rico-44-4.04x7.8",               # 44 Rico 4,04x7,8-Premium - 7900
    "roberto-44-5.6x4",               # 44 Roberto 5,6x4-Premium - 6500
    "murray-44-4x6",                  # 44 Murray 4x6-Premium - 6100
    "hakan-a-44-6x5.2",               # 44 Hakan A 6x5,2-Premium - 8600
    "erna-44-2.5x4.5",                # 44 Erna 2,5x4,5-Premium - 3100
    "eko-44-5x5.7",                   # 44 Eko 5x5,7-Premium - 7810
    "deko-44-5x3",                    # 44 Deko 5x3-Premium - 4100
    "helmand-44-3x9",                 # 44 Helmand 3x9-Premium - 7300
    "ottawa-44-6x4.5",                # 44 Ottawa 6x4,5-Premium - 7000
    "padova-a-44-6x4.5",              # 44 Padova A 6x4,5-Premium - 7700
    "milano-44-3.8x5.3",              # 44 Milano 3,8x5,3-Premium - 4440
    "trento-44-6x5",                  # 44 Trento 6x5-Premium - 7000
    "linus-44-4x4",                   # 44 Linus 4x4-Premium - 3900
    "linus-44-4x5",                   # 44 Linus 4x5-Premium - 4300
    "linus-44-5x4",                   # 44 Linus 5x4-Premium - 4400
    "linus-44-5x5",                   # 44 Linus 5x5-Premium - 4800
    "linus-44-5x4-wc",                # 44 Linus 5x4 WC-Premium - 5700
    "linus-44-5x5-wc",                # 44 Linus 5x5 WC-Premium - 6100
    "linus-44-6x4",                   # 44 Linus 6x4-Premium - 4800
    "linus-44-6x5",                   # 44 Linus 6x5-Premium - 5400
    "linus-44-6x5-wc",                # 44 Linus 6x5 WC-Premium - 6800
    "linus-44-6x6-wc",                # 44 Linus 6x6 WC-Premium - 7710
    "linus-44-6x6",                   # 44 Linus 6x6-Premium - 6100
    "scarlett-44-7x10.2",             # 44 Scarlett 7x10,2-Premium - 17000
    "almería-44-6x8.87",              # 44 Almeria 6x8,87-Premium - 12000 (сверено по реальной папке — с "í")
    "jennifer-44-10.5x8.52",          # 44 Jennifer 10,5x8,52-Premium - 18800
    "orlando-44-8x9",                 # 44 Orlando 8x9-Premium - 15200
    "lukas-44-6.5x7.7",               # 44 Lukas 6,5x7,7-Premium - 11800
    "gustav-b-44-6x8-wc",             # 44 Gustav B 6x8 WC-Premium - 15900
    "gustav-a-44-6x6-wc",             # 44 Gustav A 6x6 WC-Premium - 15000
    "louise-44-6x6",                  # 44 Louise 6x6-Premium - 11200
    "torino-44-4.5x6",                # 44 Torino 4,5x6-Premium - 9990
    "gustav-b-44-6x8",                # 44 Gustav B 6x8-Premium - 15800
    "gustav-a-44-6x6",                # 44 Gustav A 6x6-Premium - 12420
    "alma-44-7.05x8",                 # 44 Alma 7,05x8-Premium - 10900
    "ibérica-t3-44-7.92x11.84",       # 44 Ibérica T3 7,92x11,84-Premium - 20200 (сверено по реальной папке — с "é")
    "sevilla-44-7.8x13.74",           # 44 Sevilla 7,8x13,74-Premium - 25750

    # Гаражи с меткой Premium — по просьбе клиента показываются И в
    # Garajes (это уже само собой, по названию), И здесь, в Premium:
    "garaje-44-6x6",                  # 44 Garaje 6x6-Premium - 5600
    "garaje-44-3.2x5.2",              # 44 Garaje 3,2x5,2-Premium - 3500
    "garaje-44-4x6",                  # 44 Garaje 4x6-Premium - 4000
    "garaje-44-5x5",                  # 44 Garaje 5x5-Premium - 4800
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

"""
validate_data.py

Автоматически проверяет все houses/*/data.json на подозрительные
несостыковки — вместо ручной проверки каждого из 85 домов.

Проверяет:
  1. Обязательные поля на месте (name, price, thickness, size)
  2. Цена дома и цены опций (ins_roof/ins_wall/tegola) — не выбиваются
     ли аномально из общего диапазона по всем домам (как было с
     Markus: tegola=13500 при норме 250-2000)
  3. Размер в data.json совпадает с размером в specs (Ancho x largo),
     если оба поля заполнены
  4. Список фото не пустой, и все файлы из списка реально лежат в
     папке (ловит случаи, когда фото не докачались/не были
     перенесены после ручной правки)
  5. Цена опций не превышает половину базовой цены дома (ещё один
     грубый фильтр на опечатки вроде лишнего нуля)

Ничего не исправляет — только печатает отчёт по каждому найденному
подозрению, чтобы проверить руками именно эти дома, а не все 85.

Запускать из корня репозитория:
    python validate_data.py
"""

import json
import re
import statistics
from pathlib import Path

HOUSES_DIR = Path("houses")

def load_all():
    houses = []
    for path in sorted(HOUSES_DIR.glob("*/data.json")):
        slug = path.parent.name
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"[БИТЫЙ JSON] {slug}: {e}")
            continue
        houses.append((slug, path.parent, data))
    return houses


def parse_size_numbers(size_str):
    """'6.5x7.7' -> (6.5, 7.7), либо None если не распознано"""
    m = re.match(r"^(\d+(?:\.\d+)?)[xх×](\d+(?:\.\d+)?)$", size_str.strip(), re.IGNORECASE)
    if not m:
        return None
    return float(m.group(1)), float(m.group(2))


def parse_specs_dimensions(specs):
    """Ищет в specs что-то вроде 'Ancho x largo del edificio (m)': '6,5 x 7,7'"""
    for key, val in specs.items():
        if re.search(r"ancho.*largo|width.*length", key, re.IGNORECASE):
            val_norm = val.replace(",", ".")
            m = re.match(r"^(\d+(?:\.\d+)?)\s*[xх×]\s*(\d+(?:\.\d+)?)$", val_norm.strip(), re.IGNORECASE)
            if m:
                return float(m.group(1)), float(m.group(2))
    return None


def main():
    if not HOUSES_DIR.exists():
        print("Папка houses/ не найдена. Запусти скрипт из корня репозитория.")
        return

    houses = load_all()
    print(f"Загружено домов: {len(houses)}\n")

    issues = []

    # Собираем статистику по ценам опций для поиска выбросов
    option_values = {"ins_roof": [], "ins_wall": [], "tegola": []}
    for slug, folder, data in houses:
        opt = data.get("options", {})
        for key in option_values:
            if key in opt and isinstance(opt[key], (int, float)) and opt[key] > 0:
                option_values[key].append(opt[key])

    medians = {k: statistics.median(v) for k, v in option_values.items() if len(v) >= 5}

    for slug, folder, data in houses:
        local_issues = []

        # 1. Обязательные поля
        if not data.get("name"):
            local_issues.append("нет поля 'name'")
        if not data.get("price"):
            local_issues.append("цена отсутствует или равна 0")
        if not data.get("thickness"):
            local_issues.append("нет поля 'thickness'")
        size = data.get("size", "")
        if not size:
            local_issues.append("поле 'size' пустое (нет размера)")

        # 2. Выбросы по ценам опций (более чем в 4 раза выше/ниже медианы)
        opt = data.get("options", {})
        for key, val in opt.items():
            if key in medians and isinstance(val, (int, float)) and val > 0:
                med = medians[key]
                if val > med * 4 or val < med / 4:
                    local_issues.append(
                        f"опция '{key}'={val} сильно отличается от типичной "
                        f"цены по всем домам (медиана {med:.0f}) — проверить вручную"
                    )

        # 3. Опции дороже половины базовой цены дома — подозрительно
        price = data.get("price", 0)
        if price:
            for key, val in opt.items():
                if isinstance(val, (int, float)) and val > price * 0.5:
                    local_issues.append(
                        f"опция '{key}'={val} больше половины цены дома ({price}) — проверить"
                    )

        # 4. Размер в data.json vs specs
        if size:
            size_nums = parse_size_numbers(size)
            specs_nums = parse_specs_dimensions(data.get("specs", {}))
            if size_nums and specs_nums:
                # сравниваем без учёта порядка (иногда ширина/длина местами)
                a = sorted(size_nums)
                b = sorted(specs_nums)
                if abs(a[0] - b[0]) > 0.15 or abs(a[1] - b[1]) > 0.15:
                    local_issues.append(
                        f"размер в 'size' ({size}) не совпадает с размером "
                        f"в 'specs' ({specs_nums[0]}x{specs_nums[1]}) — проверить вручную"
                    )

        # 5. Фото — список не пуст, и файлы реально существуют
        photos = data.get("photos", [])
        if not photos:
            local_issues.append("список фото пуст")
        else:
            missing = [p for p in photos if not (folder / p).exists()]
            if missing:
                local_issues.append(f"{len(missing)} файлов из 'photos' физически нет в папке: {missing}")

        if local_issues:
            issues.append((slug, local_issues))

    if not issues:
        print("Подозрительных несостыковок не найдено.")
        return

    print(f"Домов с подозрениями: {len(issues)} из {len(houses)}\n")
    for slug, local_issues in issues:
        print(f"[{slug}]")
        for i in local_issues:
            print(f"    - {i}")
        print()


if __name__ == "__main__":
    main()

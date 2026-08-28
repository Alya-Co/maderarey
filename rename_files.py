#!/usr/bin/env python3
"""
Переименовывает файлы в папках houses — убирает пробелы и скобки
Обновляет data.json с новыми именами
"""
import os
import json
import re
from pathlib import Path

HOUSES_PATH = r"D:\Работа Маркетинг\Деревянные дома\Githab\maderarey\houses"

def clean_filename(name):
    """Убирает пробелы, скобки из имени файла"""
    # убираем (1), (2) и т.д.
    name = re.sub(r'\s*\(\d+\)', '', name)
    # убираем пробелы
    name = name.replace(' ', '_')
    # убираем лишние подчёркивания
    name = re.sub(r'_+', '_', name)
    return name

def process_houses():
    houses_dir = Path(HOUSES_PATH)

    for house_folder in houses_dir.iterdir():
        if not house_folder.is_dir():
            continue

        json_path = house_folder / 'data.json'
        if not json_path.exists():
            continue

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            photos = data.get('photos', [])
            new_photos = []
            changed = False

            for photo in photos:
                new_name = clean_filename(photo)
                old_file = house_folder / photo
                new_file = house_folder / new_name

                if photo == new_name:
                    new_photos.append(photo)
                    continue

                if not old_file.exists():
                    # Файл уже переименован раньше или отсутствует —
                    # просто записываем ожидаемое новое имя
                    new_photos.append(new_name)
                    continue

                if new_file.exists() and new_file != old_file:
                    # Настоящий конфликт: два РАЗНЫХ файла с одинаковым
                    # именем после очистки (Виктор иногда присылает разные
                    # фото под одинаковым базовым именем, отличая их только
                    # "(1)", "(2)"...). Раньше в этом случае имя с пробелом/
                    # скобками просто оставалось как есть — а именно такие
                    # имена не грузятся на GitHub Pages. Вместо этого даём
                    # файлу свой уникальный, но безопасный суффикс.
                    stem, ext = os.path.splitext(new_name)
                    counter = 2
                    candidate = f"{stem}_{counter}{ext}"
                    while (house_folder / candidate).exists():
                        counter += 1
                        candidate = f"{stem}_{counter}{ext}"
                    unique_file = house_folder / candidate
                    old_file.rename(unique_file)
                    print(f"  {photo} → {candidate}  (конфликт имён — добавлен суффикс _{counter})")
                    changed = True
                    new_photos.append(candidate)
                    continue

                old_file.rename(new_file)
                print(f"  {photo} → {new_name}")
                changed = True
                new_photos.append(new_name)

            if changed:
                data['photos'] = new_photos
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"✓ {house_folder.name} — обновлено")
            else:
                print(f"— {house_folder.name} — без изменений")

        except Exception as e:
            print(f"❌ {house_folder.name}: ошибка при обработке — "
                  f"{e} — пропускаю эту папку и иду дальше")
            continue

if __name__ == '__main__':
    print(f"Обрабатываю папки в: {HOUSES_PATH}\n")
    process_houses()
    print("\nГотово! Теперь сделай Commit и Push в GitHub Desktop.")

"""
generate_catalog.py

Генерирует блок карточек каталога в index.html на основе всех houses/*/data.json.
Полностью заменяет содержимое между маркерами
    <!-- CATALOG:START -->
    <!-- CATALOG:END -->
в index.html. Всё, что вручную дописано вне этих маркеров, не трогается.

Запускать из корня репозитория (там же, где index.html и houses/):
    python generate_catalog.py

Как добавить новый дом в каталог:
    1. download_houses.py — скачать письмо в houses/<slug>/
    2. rename_files.py — почистить имена файлов
    3. Убедиться, что houses/<slug>/data.json существует и заполнен
       (name, price, size, thickness, specs, photos, description)
    4. python generate_catalog.py — карточка появится в index.html сама

Категория карточки (viviendas / cabanas / casetas / garajes / premium)
берётся из необязательного поля "category" в data.json.
Если поля нет — по умолчанию "viviendas".
Чтобы дом попал в другую вкладку каталога, добавь в data.json:
    "category": "cabanas"
"""

import json
import re
from pathlib import Path
from urllib.parse import quote

HOUSES_DIR = Path("houses")
INDEX_FILE = Path("index.html")

START_MARKER = "<!-- CATALOG:START -->"
END_MARKER = "<!-- CATALOG:END -->"

FEATURED_START = "<!-- FEATURED:START -->"
FEATURED_END = "<!-- FEATURED:END -->"
FEATURED_COUNT = 4          # сколько домов показывать в карусели скидок
FEATURED_MARKUP = 1.20      # "старая" цена = текущая цена * 1.20 (скидка -17%)
FEATURED_DISCOUNT_LABEL = "-17%"

DEFAULT_CATEGORY = "viviendas"
VALID_CATEGORIES = {"viviendas", "cabanas", "casetas", "garajes", "premium"}


def esc(text):
    """Экранирует кавычки/амперсанды для безопасной вставки в HTML-атрибуты."""
    return (str(text)
            .replace("&", "&amp;")
            .replace('"', "&quot;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))


def format_price(n):
    try:
        return f"{int(n):,}".replace(",", ".") + "€"
    except (TypeError, ValueError):
        return "—"


def get_area(data):
    specs = data.get("specs", {})
    for key, val in specs.items():
        if "superficie interior" in key.lower():
            # Защита от "грязных" чисел вроде 46.5999999999999994,
            # которые иногда встречаются прямо в письме Виктора
            try:
                return f"{float(str(val).replace(',', '.')):.1f}"
            except (TypeError, ValueError):
                return val
    return None


def get_categories(slug, data):
    """Дом может попадать сразу в НЕСКОЛЬКО вкладок каталога (например,
    гараж с меткой Premium должен быть виден и во вкладке Garajes, и во
    вкладке Premium одновременно). Возвращает set() категорий.

    - "garajes" — автоматически, если в названии/слаге есть
      "garaje"/"cochera".
    - "premium" — автоматически, если в теме письма Виктора буквально
      было слово "Premium" (premium_marker в data.json, см.
      download_houses.py). Толщина стены НЕ используется.
    - Плюс к этому — всё, что явно записано в data.json в поле
      "category" (строка ИЛИ список строк) — обычно руками через
      set_category.py. Это ДОБАВЛЯЕТСЯ к автоопределению, а не
      заменяет его — так гараж, вручную добавленный в PREMIUM,
      остаётся и в Garajes тоже.
    - Если в итоге категорий не набралось ни одной — категория по
      умолчанию "viviendas".
    """
    categories = set()
    text = f"{slug} {data.get('name', '')}".lower()
    if "garaje" in text or "cochera" in text:
        categories.add("garajes")
    if data.get("premium_marker"):
        categories.add("premium")

    explicit = data.get("category")
    if explicit:
        explicit_list = [explicit] if isinstance(explicit, str) else explicit
        for c in explicit_list:
            if c in VALID_CATEGORIES:
                categories.add(c)
            else:
                print(f"  [!] {slug}: неизвестная category '{c}' в data.json — игнорирую")

    if not categories:
        categories.add(DEFAULT_CATEGORY)

    return categories


def build_card(slug, data):
    name = data.get("name", slug)
    size = data.get("size", "")
    thickness = data.get("thickness", "")
    price = data.get("price")
    photos = data.get("photos", [])
    categories = get_categories(slug, data)
    data_cat = " ".join(sorted(categories))

    area = get_area(data)

    if not photos:
        print(f"  [!] {slug}: нет фото в data.json — карточка будет без картинки")
        photo_html = ""
    else:
        first_photo = f"houses/{slug}/{photos[0]}"
        alt = esc(f"{name} {size} casa de madera {thickness}".strip())
        photo_html = f'<img src="{esc(first_photo)}" alt="{alt}" loading="lazy">'

    # Гараж с меткой Premium показывает золотой бейдж "Premium" (это его
    # главное отличие для покупателя), а не толщину стены.
    badge = "Premium" if "premium" in categories else esc(thickness)
    badge_style = ' style="background:#B8860B"' if "premium" in categories else ""

    meta_parts = []
    if size:
        meta_parts.append(f"<span>{esc(size)} m</span>")
    if area:
        meta_parts.append(f"<span>{esc(area)} m²</span>")
    meta_html = "".join(meta_parts)

    price_html = format_price(price) if price is not None else "Consultar"

    card_name_display = esc(name) + (f" {esc(size)}" if size else "")

    return f'''    <div class="card visible" data-cat="{esc(data_cat)}" data-casa="{esc(slug)}">
      <a href="house.html?casa={esc(slug)}" class="card-img-link"><div class="card-img">
        {photo_html}
        <span class="card-badge"{badge_style}>{badge}</span>
      </div></a>
      <div class="card-body">
        <div class="card-name">{card_name_display}</div>
        <div class="card-meta">{meta_html}</div>
        <div class="card-price">{price_html} <span>sin tejas/pintura</span></div>
        <a class="card-btn" href="house.html?casa={esc(slug)}">Ver ficha y precio</a>
      </div>
    </div>'''


def build_featured_slide(slug, data):
    name = data.get("name", slug)
    size = data.get("size", "")
    thickness = data.get("thickness", "")
    price = data.get("price", 0)
    photos = data.get("photos", [])

    old_price = round(price * FEATURED_MARKUP / 10) * 10  # редонд до десятков
    savings = old_price - price

    if photos:
        img_html = f'<img src="houses/{esc(slug)}/{esc(photos[0])}" alt="Casa de madera {esc(name)} oferta">'
    else:
        img_html = ""

    desc_parts = []
    if thickness:
        desc_parts.append(thickness)
    if size:
        desc_parts.append(f"{size} m")
    desc = " · ".join(desc_parts)

    # Todo el banner es un enlace a la ficha de la casa (antes solo el
    # botón llevaba a WhatsApp y el resto del banner no llevaba a
    # ninguna parte) — al hacer click en cualquier punto del banner se
    # va a house.html, no a WhatsApp.
    return f'''  <a class="oferta-banner" href="house.html?casa={esc(slug)}">
    <div class="oferta-img">{img_html}</div>
    <div class="oferta-overlay">
      <span class="oferta-tag">{FEATURED_DISCOUNT_LABEL} OFERTA</span>
      <h2 class="oferta-title">{esc(name)} {esc(size)}</h2>
      <p class="oferta-desc">{esc(desc)}</p>
      <div class="oferta-prices">
        <span class="oferta-old">{format_price(old_price)}</span>
        <span class="oferta-new">{format_price(price)}</span>
        <span class="oferta-save">Ahorras {format_price(savings)}</span>
      </div>
      <span class="oferta-btn">Ver ficha y precio</span>
    </div>
  </a>'''


def main():
    if not HOUSES_DIR.exists():
        print("Папка houses/ не найдена. Запусти скрипт из корня репозитория.")
        return
    if not INDEX_FILE.exists():
        print("index.html не найден. Запусти скрипт из корня репозитория.")
        return

    data_files = sorted(HOUSES_DIR.glob("*/data.json"))
    print(f"Найдено домов: {len(data_files)}")

    cards = []
    skipped = []
    for path in data_files:
        slug = path.parent.name
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"  [пропуск] {slug}: битый data.json ({e})")
            skipped.append(slug)
            continue

        if not data.get("name") or data.get("price") is None:
            print(f"  [пропуск] {slug}: нет name или price — карточка не создана")
            skipped.append(slug)
            continue

        cards.append((data.get("price", 0), slug, data))

    # сортируем по цене (как было в исходном каталоге — от дешёвых к дорогим)
    cards.sort(key=lambda c: c[0])

    card_html_blocks = [build_card(slug, data) for _, slug, data in cards]
    catalog_html = "\n\n".join(card_html_blocks)

    # Карусель "скидок" — берём дома с явной пометкой "featured": true
    # в data.json, а если таких нет — берём самые доступные ПОЛНОЦЕННЫЕ
    # дома по цене (пропуская гаражи/каситы/офисы — их рекламировать
    # ленее логично, чем настоящие жилые дома)
    NON_FEATURED_KEYWORDS = ["garaje", "cochera", "oficina", "caseta"]

    def looks_like_house(slug, data):
        text = f"{slug} {data.get('name', '')}".lower()
        return not any(kw in text for kw in NON_FEATURED_KEYWORDS)

    featured = [(slug, data) for _, slug, data in cards if data.get("featured")]
    if not featured:
        featured = [
            (slug, data) for _, slug, data in cards
            if data.get("photos") and looks_like_house(slug, data)
        ][:FEATURED_COUNT]
    else:
        featured = featured[:FEATURED_COUNT]
    featured_html = "\n\n".join(build_featured_slide(slug, data) for slug, data in featured)

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    if START_MARKER not in content or END_MARKER not in content:
        print(f"Не найдены маркеры {START_MARKER} / {END_MARKER} в index.html.")
        print("Добавь их вручную внутрь <div class=\"cards-grid\">...</div> один раз.")
        return

    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        re.DOTALL
    )
    new_block = f"{START_MARKER}\n\n{catalog_html}\n\n{END_MARKER}"
    new_content = pattern.sub(new_block, content, count=1)

    if FEATURED_START in new_content and FEATURED_END in new_content:
        featured_pattern = re.compile(
            re.escape(FEATURED_START) + r".*?" + re.escape(FEATURED_END),
            re.DOTALL
        )
        featured_block = f"{FEATURED_START}\n\n{featured_html}\n\n{FEATURED_END}"
        new_content = featured_pattern.sub(featured_block, new_content, count=1)
    else:
        print(f"[!] Маркеры {FEATURED_START} / {FEATURED_END} не найдены — карусель скидок не обновлена")

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"\nСоздано карточек: {len(cards)}")
    print(f"В карусели скидок: {len(featured)} домов")
    if skipped:
        print(f"Пропущено (нет данных): {len(skipped)} — {', '.join(skipped)}")
    print("Готово. index.html обновлён.")


if __name__ == "__main__":
    main()

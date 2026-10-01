#!/usr/bin/env python3
"""
Генерирует CSV-фид товаров для Meta Commerce Manager (каталог для FB/Instagram/Marketplace)
из houses/*/data.json + актуальных категорий в index.html.

Запуск: python3 generate_meta_feed.py
Результат: meta_catalog_feed.csv в корне репозитория.

Встраивается в существующий пайплайн: запускать после generate_catalog.py,
чтобы фид всегда отражал текущие категории с сайта.
"""
import re, json, csv, os, unicodedata
from urllib.parse import quote

SITE = "https://maderarey.com"
BRAND = "MaderaRey"

LABELS = {
    "viviendas": "Casa de madera",
    "cabanas": "Cabaña de madera",
    "casetas": "Caseta de madera",
    "garajes": "Garaje de madera",
}
# порядок приоритета, если у товара несколько тегов (кроме premium)
PRIORITY = ["viviendas", "cabanas", "casetas", "garajes"]

def ascii_id(slug):
    norm = unicodedata.normalize('NFKD', slug)
    return ''.join(c for c in norm if not unicodedata.combining(c))

def url_path(*parts):
    return SITE + "/" + "/".join(quote(p, safe="+") for p in parts)

# --- читаем актуальные категории прямо из каталога на сайте (источник правды) ---
html = open('index.html', encoding='utf-8').read()
start = html.index('<!-- CATALOG:START -->')
end = html.index('<!-- CATALOG:END -->')
catalog = html[start:end]
blocks = re.split(r'(?=<div class="card[^"]*" data-cat=")', catalog)

cat_by_slug = {}
for b in blocks:
    m = re.search(r'data-cat="([^"]*)" data-casa="([^"]*)"', b)
    if m:
        cat_by_slug[m.group(2)] = m.group(1).split()

rows = []
skipped = []
for slug, tokens in cat_by_slug.items():
    jpath = os.path.join('houses', slug, 'data.json')
    if not os.path.exists(jpath):
        skipped.append((slug, 'нет data.json'))
        continue
    d = json.load(open(jpath, encoding='utf-8'))
    photos = d.get('photos') or []
    if not photos:
        skipped.append((slug, 'нет фото'))
        continue

    base_cat = next((t for t in PRIORITY if t in tokens), None)
    if not base_cat:
        if 'premium' in tokens:
            # "premium"-только карточки (по факту крупные дома) — для фида считаем viviendas
            base_cat = 'viviendas'
        else:
            skipped.append((slug, f'нет базовой категории в {tokens}'))
            continue
    is_premium = 'premium' in tokens

    name = d.get('name', slug)
    size = d.get('size', '')
    price = d.get('price')
    if not price:
        skipped.append((slug, 'нет цены'))
        continue

    title = f"{LABELS[base_cat]} {name} {size}".strip()
    if len(title) > 150:
        title = title[:150]

    link = url_path('house.html') + f"?casa={quote(slug, safe='')}"
    image_link = url_path('houses', slug, photos[0])

    rows.append({
        'id': ascii_id(slug),
        'title': title,
        'description': (d.get('description') or title)[:5000],
        'availability': 'in stock',
        'condition': 'new',
        'price': f"{price:.2f} EUR",
        'link': link,
        'image_link': image_link,
        'brand': BRAND,
        'product_type': LABELS[base_cat] if not is_premium else f"{LABELS[base_cat]} > Premium",
        'custom_label_0': base_cat,
        'custom_label_1': 'premium' if is_premium else '',
    })

fields = ['id','title','description','availability','condition','price','link',
          'image_link','brand','product_type','custom_label_0','custom_label_1']

with open('meta_catalog_feed.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

print(f"Готово: {len(rows)} товаров записано в meta_catalog_feed.csv")
if skipped:
    print(f"\nПропущено {len(skipped)}:")
    for s, reason in skipped:
        print(f"  {s}: {reason}")

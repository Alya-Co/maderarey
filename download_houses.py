#!/usr/bin/env python3
"""
Скрипт для скачивания писем от Victor Musikhin (MaderaRey)
Скачивает фото, описание и характеристики каждого дома
"""

import os
import json
import base64
import re
import time
from pathlib import Path

# ── НАСТРОЙКИ ──────────────────────────────────────────────────────
SENDER_EMAIL = "info@maderarey.es"
SAVE_PATH = r"D:\Работа Маркетинг\Деревянные дома\houses_v2"
# ───────────────────────────────────────────────────────────────────

def install_deps():
    import subprocess
    subprocess.run(["pip", "install", "google-auth", "google-auth-oauthlib", 
                   "google-auth-httplib2", "google-api-python-client", 
                   "beautifulsoup4", "lxml"], check=True)

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from bs4 import BeautifulSoup
except ImportError:
    print("Устанавливаю зависимости...")
    install_deps()
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from bs4 import BeautifulSoup

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    """Авторизация в Gmail"""
    creds = None
    token_path = Path(__file__).parent / 'token.json'
    creds_path = Path(__file__).parent / 'credentials.json'
    
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not creds_path.exists():
                print("\n❌ Файл credentials.json не найден!")
                print("Следуй инструкции в README.txt")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'w') as f:
            f.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)

def parse_subject(subject):
    """
    Из темы '68 Oskar 8,87x10,04 - 25300' извлекает:
    thickness=68, name=Oskar, size=8.87x10.04, price=25300
    """
    subject = subject.strip()

    # Убираем префиксы ответа/пересылки (Re:, RE:, Fwd:, Fw: ...), могут
    # повторяться ("Re: Re: 68 Gustav...")
    subject = re.sub(r'^(re|fwd?|fw)\s*:\s*', '', subject, flags=re.IGNORECASE).strip()
    subject = re.sub(r'^(re|fwd?|fw)\s*:\s*', '', subject, flags=re.IGNORECASE).strip()

    # "oficina 44 Bergen 4,2x8-Premium" — категория-слово перед толщиной,
    # мешает регулярке искать число строго в начале строки
    category_prefix_match = re.match(r'^(oficina)\s+', subject, flags=re.IGNORECASE)
    category_prefix = category_prefix_match.group(1).lower() if category_prefix_match else ""
    if category_prefix_match:
        subject = subject[category_prefix_match.end():].strip()
    
    # Толщина в начале (44 или 68)
    thickness_match = re.match(r'^(\d+)\s+', subject)
    thickness = thickness_match.group(1) if thickness_match else "44"
    
    # Цена в конце после тире
    price_match = re.search(r'-?\s*(\d+(?:[.,]\d{3})*)\s*(?:eur|€)?\.?\s*$', subject, re.IGNORECASE)
    price = int(price_match.group(1).replace('.', '').replace(',', '')) if price_match else 0
    
    # Название и размер — между толщиной и ценой
    middle = re.sub(r'^\d+\s+', '', subject)  # убираем толщину
    middle = re.sub(r'\s*-\s*\d+(?:[.,]\d{3})*\s*(?:eur|€)?\.?\s*$', '', middle, flags=re.IGNORECASE)  # убираем цену
    middle = middle.strip()
    
    # Размер (число x число)
    size_match = re.search(r'(\d+[,.]?\d*\s*[xх×]\s*\d+[,.]?\d*)', middle, re.IGNORECASE)
    size = size_match.group(1).replace(',', '.') if size_match else ""

    # "Linus 5x4 WC-Premium" — WC (санузел) стоит ПОСЛЕ размера, поэтому
    # его нужно отдельно проверить в остатке строки, иначе WC-версия и
    # обычная версия одного размера схлопнутся в одну папку
    has_wc = False
    if size_match:
        suffix_after_size = middle[size_match.end():]
        has_wc = bool(re.search(r'\bwc\b', suffix_after_size, re.IGNORECASE))

    # Название — всё до размера
    if size_match:
        name = middle[:size_match.start()].strip()
    else:
        name = middle
    
    # Чистим название
    name = re.sub(r'[^\w\s-]', '', name).strip()
    display_name = f"{name} WC" if has_wc else name
    
    return {
        "thickness": thickness,
        "name": name,
        "display_name": display_name,
        "size": size,
        "price": price,
        "category_prefix": category_prefix,
        "has_wc": has_wc
    }

def make_folder_name(parsed):
    """Создаёт имя папки: oskar-68-8.87x10.04 (включая толщину стены,
    чтобы 44мм и 68мм версии одного размера не считались одним домом)"""
    name = parsed['name'].lower().replace(' ', '-')
    size = parsed['size'].replace(' ', '').replace(',', '.')
    thickness = parsed['thickness']
    parts = []
    if parsed.get('category_prefix'):
        parts.append(parsed['category_prefix'])
    parts.append(name)
    parts.append(thickness)
    if size:
        parts.append(size)
    if parsed.get('has_wc'):
        parts.append('wc')
    return "-".join(parts)

def extract_table_data(html_content):
    """Извлекает данные из таблицы в письме"""
    soup = BeautifulSoup(html_content, 'lxml')
    tables = soup.find_all('table')
    
    specs = {}
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True)
                value = cells[-1].get_text(strip=True)
                if key and value and key != value:
                    specs[key] = value
    
    return specs

def extract_text(html_content):
    """Извлекает текст описания из письма"""
    soup = BeautifulSoup(html_content, 'lxml')
    # Удаляем таблицы
    for table in soup.find_all('table'):
        table.decompose()
    text = soup.get_text(separator='\n', strip=True)
    # Убираем пустые строки
    lines = [l for l in text.split('\n') if l.strip()]
    return '\n'.join(lines)

def get_message_parts(service, msg_id):
    """Получает все части письма"""
    message = service.users().messages().get(
        userId='me', id=msg_id, format='full'
    ).execute()
    
    return message

def decode_base64(data):
    """Декодирует base64 данные"""
    # Gmail использует URL-safe base64
    data = data.replace('-', '+').replace('_', '/')
    padding = 4 - len(data) % 4
    if padding != 4:
        data += '=' * padding
    return base64.b64decode(data)

def process_part(part, html_parts, attachments):
    """Рекурсивно обрабатывает части письма"""
    mime_type = part.get('mimeType', '')
    
    if mime_type == 'text/html':
        data = part.get('body', {}).get('data', '')
        if data:
            html_parts.append(decode_base64(data).decode('utf-8', errors='ignore'))
    
    elif mime_type.startswith('image/') or (
        part.get('filename', '') and 
        any(part.get('filename', '').lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])
    ):
        filename = part.get('filename', '')
        attachment_id = part.get('body', {}).get('attachmentId', '')
        if filename and attachment_id:
            attachments.append({
                'filename': filename,
                'attachment_id': attachment_id
            })
    
    # Рекурсия для multipart
    for subpart in part.get('parts', []):
        process_part(subpart, html_parts, attachments)

def download_emails():
    """Основная функция"""
    print("🔐 Подключаюсь к Gmail...")
    service = get_gmail_service()
    if not service:
        return
    
    print(f"🔍 Ищу письма от {SENDER_EMAIL}...")
    
    results = service.users().messages().list(
        userId='me',
        q=f'from:{SENDER_EMAIL}',
        maxResults=200
    ).execute()
    
    messages = results.get('messages', [])
    print(f"📬 Найдено писем: {len(messages)}")
    
    if not messages:
        print("Писем не найдено.")
        return
    
    save_root = Path(SAVE_PATH)
    save_root.mkdir(parents=True, exist_ok=True)
    
    processed = 0
    skipped = 0
    
    for i, msg_ref in enumerate(messages, 1):
        msg_id = msg_ref['id']

        try:
            # Получаем письмо
            message = service.users().messages().get(
                userId='me', id=msg_id, format='full'
            ).execute()

            # Тема письма
            headers = {h['name']: h['value'] for h in message['payload']['headers']}
            subject = headers.get('Subject', 'unknown')

            print(f"\n[{i}/{len(messages)}] {subject}")

            # Парсим тему
            parsed = parse_subject(subject)
            if not parsed['name']:
                print(f"  ⚠️ Не удалось распознать название — пропускаю")
                skipped += 1
                continue

            # Создаём папку
            folder_name = make_folder_name(parsed)
            house_dir = save_root / folder_name

            # Пропускаем, только если папка уже есть, там есть data.json,
            # И в нём реально есть фото. Иначе письмо-ответ без вложений
            # (RE: ..., 0 фото) может создать "пустую" папку раньше письма
            # с настоящими фото — и то, что важнее, будет потеряно.
            existing_json = house_dir / 'data.json'
            if house_dir.exists() and existing_json.exists():
                try:
                    with open(existing_json, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                    if existing_data.get('photos'):
                        print(f"  ⏭️ Уже скачано — пропускаю")
                        skipped += 1
                        continue
                    else:
                        print(f"  🔁 Папка есть, но без фото — пробую скачать заново")
                except (json.JSONDecodeError, OSError):
                    pass

            house_dir.mkdir(exist_ok=True)
            print(f"  📁 Новая папка: {folder_name}")

            # Извлекаем части письма
            html_parts = []
            attachments = []
            process_part(message['payload'], html_parts, attachments)

            # Описание и таблица
            specs = {}
            description = ""
            if html_parts:
                html_content = '\n'.join(html_parts)
                specs = extract_table_data(html_content)
                description = extract_text(html_content)

            # Скачиваем вложения (фото)
            photos = []
            for att in attachments:
                att_data = None
                for attempt in range(4):
                    try:
                        att_data = service.users().messages().attachments().get(
                            userId='me', messageId=msg_id, id=att['attachment_id']
                        ).execute()
                        break
                    except Exception as e:
                        if attempt < 3:
                            wait = 2 ** attempt
                            print(f"  ⚠️ Ошибка Gmail API при скачивании {att['filename']}, "
                                  f"повтор через {wait}с ({attempt + 1}/3): {e}")
                            time.sleep(wait)
                        else:
                            print(f"  ❌ Не удалось скачать {att['filename']} после 3 попыток — пропускаю фото")

                if att_data is None:
                    continue

                file_data = decode_base64(att_data['data'])
                file_path = house_dir / att['filename']

                with open(file_path, 'wb') as f:
                    f.write(file_data)

                photos.append(att['filename'])
                print(f"  📷 {att['filename']}")

            # Создаём data.json
            data = {
                "name": parsed['display_name'],
                "thickness": parsed['thickness'] + "mm",
                "size": parsed['size'],
                "price": parsed['price'],
                "description": description,
                "specs": specs,
                "photos": photos,
                "whatsapp_text": f"Hola, me interesa la casa {parsed['display_name']} {parsed['size']}"
            }

            json_path = house_dir / 'data.json'
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"  ✅ data.json создан | Фото: {len(photos)} | Характеристик: {len(specs)}")
            processed += 1

        except Exception as e:
            print(f"  ❌ Ошибка при обработке письма — пропускаю это письмо и иду дальше: {e}")
            skipped += 1
            continue

    print(f"\n🎉 Готово! Обработано: {processed}, пропущено: {skipped}")
    print(f"📂 Файлы сохранены в: {SAVE_PATH}")

if __name__ == '__main__':
    download_emails()

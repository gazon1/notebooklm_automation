import os
import shutil

from pyzotero import zotero

import constants
from database import db_manager
from models import Video

# ----------------------------
# Настройки Zotero WebDAV
# ----------------------------
ZOTERO_USER_ID = constants.ZOTERO_USER_ID
ZOTERO_API_KEY = constants.ZOTERO_API_KEY
LIBRARY_TYPE = "user"  # или 'group', если группа
ATTACHMENTS_DIR = constants.PROJECT_FOLDER / "temp_zotero_attachments"
ZOTERO_COLLECTION_NAME = "YouTube Summaries"  # имя коллекции
ZOTERO_STARAGE_PATH = "/mnt/Backup/Zotero/storage/{item_id}"

# Создаём клиент
zot = zotero.Zotero(ZOTERO_USER_ID, LIBRARY_TYPE, ZOTERO_API_KEY)

# Создаём временную папку для summary
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)


# ----------------------------
# Функция: получить или создать коллекцию
# ----------------------------
def get_or_create_collection(name):
    collections = zot.collections()
    existing = next((c for c in collections if c["data"]["name"] == name), None)

    if existing:
        print(f"📁 Используем существующую коллекцию: {existing['data']['name']}")
        return existing["key"]

    # Если нет — создаём новую
    new_col = zot.create_collections([{"name": name}])
    new_key = new_col["success"]["0"]
    print(f"🆕 Создана новая коллекция: {name}")
    return new_key


# Получаем или создаём коллекцию
collection_key = get_or_create_collection(ZOTERO_COLLECTION_NAME)

# ----------------------------
# Берём все видео с summary
# ----------------------------
with db_manager.session_scope() as session:
    videos = session.query(Video).filter(Video.summary.isnot(None)).all()

    for video in videos:
        print(f"📌 Обрабатываем: {video.title}")

        # Создаём файл с summary
        filename = f"{video.youtube_id or video.id}_summary.txt"
        filepath = os.path.join(ATTACHMENTS_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(video.summary)

        # Создаём элемент в Zotero
        item = zot.item_template("document")  # тип документа можно изменить
        item["title"] = video.title
        item["tags"] = [{"tag": "YouTube Summary"}]
        item["url"] = video.url
        item["collections"] = [collection_key]

        created_item = zot.create_items([item])

        # Загружаем attachment через WebDAV
        created_key = created_item["success"]["0"]

        res = zot.attachment_simple([filepath], parentid=created_key)
        dir_name = res["unchanged"][0]["key"]
        dir_new = ZOTERO_STARAGE_PATH.format(item_id=dir_name)
        os.makedirs(dir_new, exist_ok=True)
        shutil.move(filepath, dir_new)
        print(f"✅ Summary сохранён в Zotero: {video.title}")

print("🎉 Все summary загружены!")

import re

from database import db_manager
from models import ProcessingStatus, Video


def extract_youtube_id(url: str) -> str | None:
    """Извлекает ID видео из YouTube-ссылки"""
    match = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url)
    return match.group(1) if match else None


def parse_line(line: str) -> tuple[str, str] | None:
    """
    Разделяет строку из файла на (title, url)
    Примеры:
        "Иван Иванов - Как стать LLM экспертом - https://www.youtube.com/watch?v=xxxx"
        "Название | Автор - https://youtu.be/yyyy"
    """
    line = line.strip()
    if not line:
        return None

    url = line.split("|")[-1]
    title = line[: -(len(url) + 1)]
    return title, url


def parse_line2(line: str) -> tuple[str, str] | None:
    """
    Разделяет строку из файла на (title, url)
    Примеры:
        "Иван Иванов - Как стать LLM экспертом - https://www.youtube.com/watch?v=xxxx"
        "Название | Автор - https://youtu.be/yyyy"
    """
    line = line.strip()
    if not line:
        return None

    splitted = line.split("\\t")
    try:
        url = splitted[-1]
        title = splitted[-2]
    except IndexError:
        import ipdb

        ipdb.set_trace()
    return title, url


def import_videos_from_file(filename="videos.txt"):
    """Импортирует данные из текстового файла в БД"""
    db_manager.create_tables()

    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    added, skipped = 0, 0

    with db_manager.session_scope() as session:
        for line in lines:
            if line.startswith(("WARNING", "ERROR")):
                continue
            # parsed = parse_line(line)
            parsed = parse_line2(line)

            if not parsed:
                continue

            title, url = parsed
            youtube_id = extract_youtube_id(url)

            # Проверяем, есть ли уже такое видео
            exists = session.query(Video).filter_by(url=url).first()
            if exists:
                skipped += 1
                continue

            video = Video(
                title=title,
                url=url,
                youtube_id=youtube_id,
                status=ProcessingStatus.DOWNLOADED,
            )
            session.add(video)
            added += 1

    print(f"✅ Добавлено: {added}, пропущено (уже в БД): {skipped}")


if __name__ == "__main__":
    # import_videos_from_file("youtube_video_links.txt")
    import_videos_from_file("videos_list2.txt")

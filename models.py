import enum

from sqlalchemy import Column, Enum, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class ProcessingStatus(enum.Enum):
    """Статусы обработки видео"""

    DOWNLOADED = "downloaded"  # Просто скачана с YouTube
    SENT_TO_NOTEBOOKLM = "notebooklm"  # Отправлена в NotebookLM
    SENT_TO_ZOTERO = "zotero"  # Отправлена в Zotero
    COMPLETED = "completed"  # Обработана везде


class Video(Base):
    """Таблица для хранения информации о видео"""

    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Основная информация о видео
    title = Column(String(500), nullable=False)
    url = Column(String(500), nullable=True)
    summary = Column(Text, nullable=True)

    # Технические поля
    youtube_id = Column(String(20), nullable=True)  # ID видео на YouTube

    # Статусы обработки
    status = Column(Enum(ProcessingStatus), default=ProcessingStatus.DOWNLOADED)

    # Поля для интеграций
    notebooklm_document_id = Column(String(100))  # ID документа в NotebookLM
    zotero_item_id = Column(String(100))  # ID элемента в Zotero

    def __repr__(self) -> str:
        return (
            f"<Video(id={self.id}, title='{self.title[:30]}...', "
            f"status={self.status.value}, summary={'yes' if self.summary else 'no'})>"
        )

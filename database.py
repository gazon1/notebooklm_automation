from contextlib import contextmanager

from loguru import logger
from models import Base, Video
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker


class DatabaseManager:
    def __init__(self, db_url="sqlite:///youtube_videos.db"):
        self.engine = create_engine(db_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        """Создает все таблицы"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Таблицы созданы успешно")

    def drop_tables(self):
        """Удаляет все таблицы"""
        Base.metadata.drop_all(bind=self.engine)
        logger.info("Таблицы удалены")

    @contextmanager
    def session_scope(self):
        """Контекстный менеджер для сессий"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка в сессии: {e}")
            raise
        finally:
            session.close()

    def table_exists(self, table_name):
        """Проверяет существование таблицы"""
        inspector = inspect(self.engine)
        return table_name in inspector.get_table_names()

    def video_exists_by_title(self, title: str) -> bool:
        """
        Проверяет, существует ли в базе данных запись с данным title.
        """
        logger.info(f"Проверка существования видео с заголовком: '{title[:30]}...'")
        try:
            with self.session_scope() as session:
                # Используем statement API (SELECT) для более чистого кода
                stmt = select(Video).where(Video.title == title, Video.summary.isnot(None))

                # Используем .one_or_none() для эффективной проверки существования
                video = session.execute(stmt).scalars().first()

                if video:
                    logger.warning(f"⚠️ Видео с заголовком '{title[:30]}...' уже существует (ID: {video.id}).")
                    return True
                return False

        except Exception as e:
            # session_scope обработает rollback, если ошибка возникла внутри блока with
            logger.error(f"❌ Ошибка при проверке существования видео по title: {e}")
            return False

    def insert_video(self, **kwargs) -> None:
        """
        Создает и вставляет новый объект Video в базу данных.

        Принимает аргументы, соответствующие полям класса Video.
        Возвращает объект Video или None в случае ошибки.
        """
        try:
            with self.session_scope() as session:
                # Создание экземпляра Video
                new_video = Video(**kwargs)

                # Добавление и фиксация (commit происходит в session_scope)
                session.add(new_video)
                session.flush()  # Принудительно вставляет, чтобы получить ID
                session.refresh(new_video)  # Обновляет объект с ID

                logger.info(f"✅ Видео '{new_video.title[:30]}...' (ID: {new_video.id}) успешно добавлено.")
                return None
        except IntegrityError as e:
            logger.error(f"❌ Ошибка целостности данных: URL уже существует или нарушено другое ограничение. {e}")
            return None
        except Exception as e:
            # Ошибки, не связанные с целостностью, обрабатываются в session_scope и перебрасываются
            logger.error(f"❌ Непредвиденная ошибка при вставке видео: {e}")
            return None

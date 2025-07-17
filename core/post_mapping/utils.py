import sqlite3
import re
from pathlib import Path


def ensure_post_database_exists(db_path) -> bool:
    """Проверяет существование базы и её структуру, создаёт новую при необходимости"""

    # Подключаемся к базе (она будет создана автоматически, если не существует)
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
    except Exception as e:
        print(e)
        return False

    try:
        # Проверяем существование таблицы posts
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='posts';")
        table_exists = cursor.fetchone()

        if table_exists:
            # Проверяем структуру существующей таблицы
            cursor.execute("PRAGMA table_info(posts);")
            columns = cursor.fetchall()

            # Ожидаемые столбцы и их свойства
            expected_columns = {
                'id': {'type': 'INTEGER', 'pk': 1},
                'creator_name': {'type': 'TEXT', 'pk': 0},
                'post_id': {'type': 'TEXT', 'pk': 0},
                'post_path': {'type': 'TEXT', 'pk': 0},
                'created_at': {'type': 'TEXT', 'pk': 0}  # SQLite хранит дату как TEXT
            }

            # Проверяем столбцы
            existing_columns = {}
            for col in columns:
                existing_columns[col[1]] = {
                    'type': col[2].upper(),
                    'pk': col[5]
                }

            if existing_columns != expected_columns:
                raise ValueError("Database is corrupted: Структура таблицы 'posts' не соответствует ожидаемой")

            cursor.execute("PRAGMA index_list(posts);")
            indexes = cursor.fetchall()

            # Ищем составной unique индекс для post_id и creator_name
            found_composite_unique = False
            for index in indexes:
                if index[2]:  # unique == 1
                    cursor.execute(f"PRAGMA index_info({index[1]});")
                    index_info = cursor.fetchall()
                    if len(index_info) == 2:
                        columns_in_index = {info[2] for info in index_info}
                        if columns_in_index == {'post_id', 'creator_name'}:
                            found_composite_unique = True
                            break

            if not found_composite_unique:
                raise ValueError("Database is corrupted: "
                                 "Отсутствует составной unique индекс для post_id и creator_name")

            required_indexes = {'creator_name', 'post_id'}
            existing_single_indexes = set()

            for index in indexes:
                if not index[2]:  # unique == 0
                    cursor.execute(f"PRAGMA index_info({index[1]});")
                    index_info = cursor.fetchall()
                    if len(index_info) == 1:
                        existing_single_indexes.add(index_info[0][2])

            if not required_indexes.issubset(existing_single_indexes):
                raise ValueError("Database is corrupted: Отсутствуют необходимые индексы")

            return True

        else:
            # Создаём новую таблицу с нужной структурой
            cursor.execute("""
                CREATE TABLE posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    creator_name TEXT NOT NULL,
                    post_id TEXT NOT NULL,
                    post_path TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE (post_id, creator_name)
                );
            """)

            # Создаём индексы
            cursor.execute("CREATE INDEX idx_creator_name ON posts (creator_name);")
            cursor.execute("CREATE INDEX idx_post_id ON posts (post_id);")

            conn.commit()
            return True

    except Exception as e:
        conn.rollback()
        print(e)
        return False
    finally:
        conn.close()


def validate_windows_dir_name(dir_name: str) -> "str | None":
    """
    Проверяет и исправляет имя директории для Windows.
    Возвращает корректное имя директории.
    """
    # Запрещенные символы в именах директорий Windows
    illegal_chars = r'[<>:"/\\|?*\x00-\x1f]'

    # Зарезервированные имена в Windows
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }

    # Заменяем запрещенные символы на подчеркивание
    clean_name = re.sub(illegal_chars, '_', dir_name)

    # Удаляем ведущие и завершающие пробелы и точки
    clean_name = clean_name.strip(' .')

    # Проверяем на зарезервированные имена
    base_name = Path(clean_name).stem.upper()
    if base_name in reserved_names:
        clean_name = f"_{clean_name}_post"

    if not clean_name:
        return None

    # Ограничиваем длину имени (макс. 255 символов для NTFS)
    clean_name = clean_name[:255]

    return clean_name

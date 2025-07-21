import sqlite3
from datetime import datetime
from os import PathLike
from typing import List, Optional, Dict, Any
from datetime import UTC


class PostDBClient:
    def __init__(self, db_path: PathLike[str]):
        self._db_path = db_path
        self._db_conn: "sqlite3.Connection | None" = None
        self._closed = False

    def _get_connection(self):
        if self._closed:
            raise Exception("Can't get sqlite3 connection from closed client")
        if self._db_conn is None:
            self._db_conn = sqlite3.connect(self._db_path)
        return self._db_conn

    @property
    def closed(self):
        return self._closed

    def close(self):
        if not self._closed and self._db_conn:
            self._db_conn.close()
            self._db_conn = None
            self._closed = True

    def _get_cursor(self):
        conn = self._get_connection()
        return conn.cursor()

    def _commit(self):
        if self._db_conn:
            self._db_conn.commit()
        else:
            raise Exception("Can't commit closed connection")

    def create_post(self, creator_name: str, post_path: str, post_id: str) -> Dict[str, Any]:
        created_at = datetime.now(UTC)
        cursor = self._get_cursor()
        try:
            cursor.execute("""
                INSERT INTO posts (creator_name, post_id, post_path, created_at)
                VALUES (?, ?, ?, ?)
            """, (creator_name, post_id, post_path, created_at))
            self._commit()

            return {
                "id": cursor.lastrowid,
                "creator_name": creator_name,
                "post_id": post_id,
                "post_path": post_path,
                "created_at": created_at
            }
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Ошибка при создании поста: {e}")
        finally:
            cursor.close()

    def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Получает пост по его ID"""
        cursor = self._get_cursor()
        try:

            cursor.execute("""
                SELECT id, creator_name, post_id, post_path, created_at
                FROM posts
                WHERE post_id = ?
            """, (post_id,))

            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "creator_name": row[1],
                    "post_id": row[2],
                    "post_path": row[3],
                    "created_at": row[4]
                }
            return None
        finally:
            cursor.close()

    def get_posts_by_path(self, post_path: str) -> List[Dict[str, Any]]:
        cursor = self._get_cursor()
        try:
            cursor.execute("""
                SELECT id, creator_name, post_id, post_path, created_at
                FROM posts
                WHERE post_path = ?
                ORDER BY created_at DESC
            """, (post_path,))

            return [{
                "id": row[0],
                "creator_name": row[1],
                "post_id": row[2],
                "post_path": row[3],
                "created_at": row[4]
            } for row in cursor.fetchall()]
        finally:
            cursor.close()


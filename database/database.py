# app/database.py

import sqlite3
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional

# Путь к файлу базы данных
DB_PATH = "users.db"

# Глобальная блокировка для потокобезопасности
_db_lock = threading.Lock()


def init_db() -> Dict[str, Any]:
    """
    Инициализирует SQLite базу данных и возвращает объект для работы с ней
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    
    # Создаем таблицу пользователей, если она не существует
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            login TEXT NOT NULL,
            password TEXT NOT NULL,
            active BOOLEAN DEFAULT 1,
            next_poll_at TIMESTAMP,
            poll_failures INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    
    # Возвращаем словарь с функциями для работы с базой данных
    return {
        "conn": conn,
        "add_user": lambda telegram_id, login, password: _add_user(telegram_id, login, password, conn),
        "get_all_user_ids": lambda: _get_all_user_ids(conn),
        "get_user": lambda telegram_id: _get_user(telegram_id, conn),
        "update_user": lambda telegram_id, **kwargs: _update_user(telegram_id, conn, **kwargs),
        "load_all_users": lambda: _load_all_users(conn)
    }


def _add_user(telegram_id: int, login: str, password: str, conn: sqlite3.Connection):
    """Добавляет нового пользователя в базу данных"""
    with _db_lock:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO users (telegram_id, login, password, active, next_poll_at, poll_failures, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                telegram_id, login, password, True, datetime.utcnow(), 0, datetime.utcnow()
            ))
            conn.commit()
        except Exception as e:
            print(f"Error adding user to database: {e}")


def _get_all_user_ids(conn: sqlite3.Connection) -> List[int]:
    """Возвращает список всех ID пользователей"""
    with _db_lock:
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_id FROM users")
        return [row[0] for row in cursor.fetchall()]


def _get_user(telegram_id: int, conn: sqlite3.Connection) -> Optional[Dict[str, Any]]:
    """Возвращает информацию о пользователе по его ID"""
    with _db_lock:
        cursor = conn.cursor()
        cursor.execute("SELECT login, password, active, next_poll_at, poll_failures, created_at FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cursor.fetchone()
        if row:
            return {
                "login": row[0],
                "password": row[1],
                "active": bool(row[2]),
                "next_poll_at": datetime.fromisoformat(row[3]) if row[3] else None,
                "poll_failures": row[4],
                "created_at": datetime.fromisoformat(row[5]) if row[5] else None
            }
        return None


def _update_user(telegram_id: int, conn: sqlite3.Connection, **kwargs):
    """Обновляет информацию о пользователе"""
    with _db_lock:
        cursor = conn.cursor()
        # Формируем SQL-запрос динамически в зависимости от переданных параметров
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [telegram_id]
        query = f"UPDATE users SET {set_clause} WHERE telegram_id = ?"
        try:
            cursor.execute(query, values)
            conn.commit()
        except Exception as e:
            print(f"Error updating user in database: {e}")


def _load_all_users(conn: sqlite3.Connection) -> Dict[int, Dict[str, Any]]:
    """Загружает всех пользователей из базы данных"""
    with _db_lock:
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_id, login, password, active, next_poll_at, poll_failures, created_at FROM users")
        users = {}
        for row in cursor.fetchall():
            users[row[0]] = {
                "login": row[1],
                "password": row[2],
                "active": bool(row[3]),
                "next_poll_at": datetime.fromisoformat(row[4]) if row[4] else None,
                "poll_failures": row[5],
                "created_at": datetime.fromisoformat(row[6]) if row[6] else None
            }
        return users

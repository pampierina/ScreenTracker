"""Manejo de la base de datos SQLite para ScreenTracker."""
from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, date
from pathlib import Path
from platformdirs import user_data_dir

APP_NAME = "ScreenTracker"
APP_AUTHOR = "TuNombre"

class Database:
    def __init__(self) -> None:
        data_dir = Path(user_data_dir(APP_NAME, APP_AUTHOR))
        data_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = data_dir / "screentracker.db"
        self._conn: sqlite3.Connection | None = None
        # 🔒 Candado para que dos hilos no escriban a la vez
        self._lock = threading.Lock() 
        self.init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            # check_same_thread=False permite usar la BD en hilos diferentes
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def init_db(self) -> None:
        with self._lock: # 🔒 Bloqueamos mientras inicializamos
            with self._get_conn() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        app_name TEXT NOT NULL,
                        process_name TEXT NOT NULL,
                        pid INTEGER,
                        start_time TIMESTAMP NOT NULL,
                        end_time TIMESTAMP,
                        duration_seconds INTEGER DEFAULT 0
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    )
                """)
                
                cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('tracking_enabled', '1')")
                conn.commit()

    def insert_session(self, app_name: str, process_name: str, pid: int, start_time: datetime, duration_seconds: int) -> int:
        with self._lock: # 🔒 Bloqueamos mientras escribimos
            with self._get_conn() as conn:
                cursor = conn.cursor()
                end_time = start_time
                cursor.execute("""
                    INSERT INTO sessions (app_name, process_name, pid, start_time, end_time, duration_seconds)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (app_name, process_name, pid, start_time, end_time, duration_seconds))
                return cursor.lastrowid

    def get_tracking_enabled(self) -> bool:
        with self._lock: # 🔒 Bloqueamos mientras leemos
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM settings WHERE key = 'tracking_enabled'")
                row = cursor.fetchone()
                return row["value"] == "1" if row else True

    def set_tracking_enabled(self, enabled: bool) -> None:
        with self._lock:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                val = "1" if enabled else "0"
                cursor.execute("UPDATE settings SET value = ? WHERE key = 'tracking_enabled'", (val,))
                conn.commit()

    def get_daily_summary(self, target_date: date) -> list[dict]:
        date_str = target_date.strftime("%Y-%m-%d")
        with self._lock:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT app_name, SUM(duration_seconds) as total_seconds
                    FROM sessions
                    WHERE DATE(start_time) = ?
                    GROUP BY app_name
                    ORDER BY total_seconds DESC
                """, (date_str,))
                return [dict(row) for row in cursor.fetchall()]

    def close(self) -> None:
        with self._lock:
            if self._conn:
                self._conn.close()
                self._conn = None
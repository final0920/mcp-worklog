"""Cursor 会话采集适配器"""

import json
import os
import sqlite3
from datetime import date, datetime
from pathlib import Path

from mcp_worklog.domain.session import AISession, SessionSource


class CursorCollector:
    """Cursor 会话采集器"""

    def __init__(self, base_path: Path | None = None) -> None:
        appdata = os.environ.get("APPDATA", "")
        default_path = Path(appdata) / "Cursor" / "User" / "workspaceStorage"
        self.base_path = base_path or default_path

    def collect(self, target_date: date) -> list[AISession]:
        """采集指定日期的 Cursor 会话"""
        sessions: list[AISession] = []

        if not self.base_path.exists():
            return sessions

        # 遍历工作区目录
        for workspace_dir in self.base_path.iterdir():
            if not workspace_dir.is_dir():
                continue

            db_path = workspace_dir / "state.vscdb"
            if not db_path.exists():
                continue

            workspace_sessions = self._parse_db(db_path, target_date)
            sessions.extend(workspace_sessions)

        return sessions

    def _parse_db(self, db_path: Path, target_date: date) -> list[AISession]:
        """解析 SQLite 数据库"""
        sessions: list[AISession] = []

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value FROM ItemTable WHERE key = 'composer.composerData'"
            )
            row = cursor.fetchone()
            conn.close()

            if not row:
                return sessions

            data = json.loads(row[0])
            composers = data.get("allComposers", [])

            for composer in composers:
                created_at = composer.get("createdAt")
                if not created_at:
                    continue

                start_time = datetime.fromtimestamp(created_at / 1000)
                if start_time.date() != target_date:
                    continue

                sessions.append(
                    AISession(
                        source=SessionSource.CURSOR,
                        session_id=composer.get("composerId", ""),
                        start_time=start_time,
                        title=composer.get("name"),
                        message_count=0,  # Cursor 不直接存储消息数
                    )
                )

        except (sqlite3.Error, json.JSONDecodeError, KeyError, OSError):
            pass

        return sessions

"""Kiro 会话采集适配器"""

import json
import os
from datetime import date, datetime
from pathlib import Path

from mcp_worklog.domain.session import AISession, SessionSource


class KiroCollector:
    """Kiro 会话采集器"""

    def __init__(self, base_path: Path | None = None) -> None:
        appdata = os.environ.get("APPDATA", "")
        default_path = Path(appdata) / "Kiro" / "User" / "globalStorage" / "kiro.kiroagent"
        self.base_path = base_path or default_path

    def collect(self, target_date: date) -> list[AISession]:
        """采集指定日期的 Kiro 会话"""
        sessions: list[AISession] = []

        if not self.base_path.exists():
            return sessions

        # 遍历工作区目录
        for workspace_dir in self.base_path.iterdir():
            if not workspace_dir.is_dir():
                continue

            # 查找 .chat 文件
            for chat_file in workspace_dir.glob("*.chat"):
                session = self._parse_session(chat_file, target_date)
                if session:
                    sessions.append(session)

        return sessions

    def _parse_session(self, file_path: Path, target_date: date) -> AISession | None:
        """解析单个会话文件"""
        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            metadata = data.get("metadata", {})
            start_time_ms = metadata.get("startTime")
            if not start_time_ms:
                return None

            start_time = datetime.fromtimestamp(start_time_ms / 1000)
            if start_time.date() != target_date:
                return None

            chat_messages = data.get("chat", [])
            # 提取用户消息内容（Kiro 使用 "human" 作为用户角色）
            title = None
            user_messages: list[str] = []
            for msg in chat_messages:
                role = msg.get("role", "")
                if role in ("user", "human"):
                    content = msg.get("content", "")
                    if isinstance(content, str) and content.strip():
                        # 跳过系统提示词
                        if content.startswith("# System Prompt"):
                            continue
                        if title is None:
                            title = content[:50]
                        user_messages.append(content.strip()[:200])

            return AISession(
                source=SessionSource.KIRO,
                session_id=file_path.stem,
                start_time=start_time,
                title=title,
                message_count=len(chat_messages),
                messages=user_messages,
            )
        except (json.JSONDecodeError, KeyError, OSError):
            return None

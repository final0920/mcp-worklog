"""Claude Code 会话采集适配器"""

import json
from datetime import date, datetime
from pathlib import Path

from mcp_worklog.domain.session import AISession, SessionSource


class ClaudeCodeCollector:
    """Claude Code 会话采集器"""

    def __init__(self, base_path: Path | None = None) -> None:
        self.base_path = base_path or Path.home() / ".claude" / "projects"

    def collect(self, target_date: date) -> list[AISession]:
        """采集指定日期的 Claude Code 会话"""
        sessions: list[AISession] = []

        if not self.base_path.exists():
            return sessions

        # 遍历所有项目目录
        for project_dir in self.base_path.iterdir():
            if not project_dir.is_dir():
                continue

            # 查找 .jsonl 会话文件
            for session_file in project_dir.glob("*.jsonl"):
                session = self._parse_session(session_file, target_date)
                if session:
                    sessions.append(session)

        return sessions

    def _parse_session(self, file_path: Path, target_date: date) -> AISession | None:
        """解析单个会话文件"""
        try:
            messages = []
            first_timestamp = None
            title = None

            with file_path.open("r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    msg = json.loads(line)
                    ts = msg.get("timestamp")
                    if ts:
                        # timestamp 可能是 ISO 字符串或毫秒数
                        if isinstance(ts, str):
                            msg_time = datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
                        else:
                            msg_time = datetime.fromtimestamp(ts / 1000)
                        if msg_time.date() == target_date:
                            messages.append(msg)
                            if first_timestamp is None:
                                first_timestamp = msg_time
                            # 尝试获取标题（第一条用户消息）
                            if title is None and msg.get("type") == "human":
                                content = msg.get("message", {}).get("content", "")
                                if isinstance(content, str) and content:
                                    title = content[:50]

            if not messages:
                return None

            # 提取用户消息内容
            user_messages: list[str] = []
            for msg in messages:
                if msg.get("type") == "human":
                    content = msg.get("message", {}).get("content", "")
                    if isinstance(content, str) and content.strip():
                        user_messages.append(content.strip()[:200])

            return AISession(
                source=SessionSource.CLAUDE_CODE,
                session_id=file_path.stem,
                start_time=first_timestamp,
                title=title,
                message_count=len(messages),
                messages=user_messages,
            )
        except (json.JSONDecodeError, KeyError, OSError, ValueError):
            return None

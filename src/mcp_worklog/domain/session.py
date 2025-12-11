"""领域模型 - AI 会话"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class SessionSource(Enum):
    """会话来源"""

    CLAUDE_CODE = "claude_code"
    KIRO = "kiro"
    CURSOR = "cursor"


@dataclass
class AISession:
    """AI 会话记录"""

    source: SessionSource
    session_id: str
    start_time: datetime
    title: str | None = None
    message_count: int = 0
    messages: list[str] | None = None  # 用户消息内容列表

    @property
    def summary(self) -> str:
        """生成会话摘要"""
        title_part = self.title or "无标题"
        return f"[{self.source.value}] {title_part} ({self.message_count} 条消息)"

    @property
    def content_summary(self) -> str:
        """返回会话内容摘要（用于 LLM 总结）"""
        if not self.messages:
            return ""
        return "\n".join(f"- {msg}" for msg in self.messages[:20])  # 限制前20条

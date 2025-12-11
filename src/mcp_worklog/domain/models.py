"""领域模型 - WorkLogEntry 和 DailyDigest"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Self


@dataclass(frozen=True)
class WorkLogEntry:
    """工作记录条目（值对象）"""

    content: str
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        if not self.content or not self.content.strip():
            raise ValueError("工作记录内容不能为空")


@dataclass
class DailyDigest:
    """日报汇总（聚合根）"""

    date: date
    entries: list[WorkLogEntry] = field(default_factory=list)

    def append(self, entry: WorkLogEntry) -> None:
        """追加工作记录"""
        self.entries.append(entry)

    @property
    def entry_count(self) -> int:
        return len(self.entries)

    def get_entry_contents(self) -> list[str]:
        """获取所有条目内容列表"""
        return [e.content for e in self.entries]

    @classmethod
    def empty(cls, target_date: date) -> Self:
        """创建空日报"""
        return cls(date=target_date, entries=[])

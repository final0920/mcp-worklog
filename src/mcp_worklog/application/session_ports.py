"""出站端口 - 会话采集"""

from datetime import date
from typing import Protocol

from mcp_worklog.domain.session import AISession


class SessionCollectorPort(Protocol):
    """会话采集端口"""

    def collect(self, target_date: date) -> list[AISession]:
        """采集指定日期的会话"""
        ...

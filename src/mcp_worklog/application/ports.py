"""端口定义 - 出站端口接口"""

from abc import ABC, abstractmethod
from datetime import date
from pathlib import Path
from typing import Protocol

from mcp_worklog.domain import DailyDigest


class StoragePort(Protocol):
    """存储端口 - 日报持久化抽象"""

    def save(self, digest: DailyDigest) -> Path:
        """保存日报，返回文件路径"""
        ...

    def load(self, target_date: date) -> DailyDigest | None:
        """加载指定日期的日报，不存在返回 None"""
        ...

    def exists(self, target_date: date) -> bool:
        """检查指定日期的日报是否存在"""
        ...

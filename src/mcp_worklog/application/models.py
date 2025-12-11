"""应用层结果模型"""

from dataclasses import dataclass


@dataclass
class AppendResult:
    """追加工作记录的结果"""

    success: bool
    file_path: str
    entry_number: int
    message: str


@dataclass
class DigestResult:
    """获取日报的结果"""

    date: str
    content: str
    entry_count: int
    found: bool


@dataclass
class PolishResult:
    """润色日报的结果"""

    success: bool
    date: str
    content: str
    original_count: int
    polished_count: int

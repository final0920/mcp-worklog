"""出站适配器 - 本地文件存储"""

from datetime import date
from pathlib import Path

from mcp_worklog.domain import DailyDigest, DigestFormatter


class LocalFileStorage:
    """本地文件存储适配器"""

    FILE_EXTENSION = ".txt"
    DATE_FORMAT = "%Y-%m-%d"

    def __init__(self, base_path: Path) -> None:
        self.base_path = base_path
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        """确保存储目录存在"""
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, target_date: date) -> Path:
        """获取指定日期的文件路径"""
        filename = f"{target_date.strftime(self.DATE_FORMAT)}{self.FILE_EXTENSION}"
        return self.base_path / filename

    def save(self, digest: DailyDigest) -> Path:
        """保存日报到文件"""
        file_path = self._get_file_path(digest.date)
        content = DigestFormatter.format(digest)
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def load(self, target_date: date) -> DailyDigest | None:
        """加载指定日期的日报"""
        file_path = self._get_file_path(target_date)
        if not file_path.exists():
            return None
        content = file_path.read_text(encoding="utf-8")
        return DigestFormatter.parse(content, target_date)

    def exists(self, target_date: date) -> bool:
        """检查指定日期的日报是否存在"""
        return self._get_file_path(target_date).exists()

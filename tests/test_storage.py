"""存储适配器单元测试"""

import sys
import tempfile
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_worklog.adapters.outbound.storage import LocalFileStorage
from mcp_worklog.domain import DailyDigest, WorkLogEntry


class TestLocalFileStorage:
    """LocalFileStorage 单元测试"""

    def test_directory_auto_creation(self, tmp_path: Path):
        """测试目录自动创建"""
        storage_path = tmp_path / "worklogs" / "nested"
        assert not storage_path.exists()

        storage = LocalFileStorage(storage_path)
        assert storage_path.exists()

    def test_save_creates_file(self, tmp_path: Path):
        """测试保存创建文件"""
        storage = LocalFileStorage(tmp_path)
        digest = DailyDigest(
            date=date(2024, 12, 11),
            entries=[WorkLogEntry(content="完成任务A")],
        )

        file_path = storage.save(digest)

        assert file_path.exists()
        assert file_path.name == "2024-12-11.txt"

    def test_load_existing_file(self, tmp_path: Path):
        """测试加载已存在的文件"""
        storage = LocalFileStorage(tmp_path)
        original = DailyDigest(
            date=date(2024, 12, 11),
            entries=[
                WorkLogEntry(content="任务1"),
                WorkLogEntry(content="任务2"),
            ],
        )
        storage.save(original)

        loaded = storage.load(date(2024, 12, 11))

        assert loaded is not None
        assert loaded.date == original.date
        assert loaded.get_entry_contents() == original.get_entry_contents()

    def test_load_nonexistent_file(self, tmp_path: Path):
        """测试加载不存在的文件"""
        storage = LocalFileStorage(tmp_path)

        loaded = storage.load(date(2024, 1, 1))

        assert loaded is None

    def test_exists_true(self, tmp_path: Path):
        """测试文件存在检查 - 存在"""
        storage = LocalFileStorage(tmp_path)
        digest = DailyDigest(date=date(2024, 12, 11), entries=[])
        storage.save(digest)

        assert storage.exists(date(2024, 12, 11)) is True

    def test_exists_false(self, tmp_path: Path):
        """测试文件存在检查 - 不存在"""
        storage = LocalFileStorage(tmp_path)

        assert storage.exists(date(2024, 1, 1)) is False

"""属性测试 - 验证正确性属性"""

import sys
import tempfile
from datetime import date, datetime
from pathlib import Path

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_worklog.domain import DailyDigest, DigestFormatter, WorkLogEntry


# 生成有效的工作记录内容（非空、无换行）
valid_content = st.text(
    alphabet=st.characters(blacklist_categories=["Cc", "Cs"], blacklist_characters="\n\r"),
    min_size=1,
    max_size=200,
).filter(lambda x: x.strip())


@st.composite
def daily_digest_strategy(draw):
    """生成随机 DailyDigest"""
    target_date = draw(st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31)))
    contents = draw(st.lists(valid_content, min_size=0, max_size=10))
    entries = [WorkLogEntry(content=c, created_at=datetime.now()) for c in contents]
    return DailyDigest(date=target_date, entries=entries)


class TestProperty5RoundTripConsistency:
    """
    **Feature: mcp-worklog, Property 5: Round-Trip Consistency**
    **Validates: Requirements 5.1, 5.2**

    For any valid DailyDigest, formatting to text then parsing back
    SHALL produce an equivalent DailyDigest (same date, same entry contents).
    """

    @settings(max_examples=100)
    @given(digest=daily_digest_strategy())
    def test_format_then_parse_preserves_content(self, digest: DailyDigest):
        # 格式化
        text = DigestFormatter.format(digest)

        # 解析回来
        parsed = DigestFormatter.parse(text, digest.date)

        # 验证日期相同
        assert parsed.date == digest.date

        # 验证条目内容相同
        original_contents = digest.get_entry_contents()
        parsed_contents = parsed.get_entry_contents()
        assert parsed_contents == original_contents



class TestProperty3FileFormatConsistency:
    """
    **Feature: mcp-worklog, Property 3: File Format Consistency**
    **Validates: Requirements 5.1, 5.2**

    For any DailyDigest, the formatted text output SHALL start with
    the date line followed by a blank line, then numbered entries starting from 1.
    """

    @settings(max_examples=100)
    @given(digest=daily_digest_strategy())
    def test_format_structure(self, digest: DailyDigest):
        text = DigestFormatter.format(digest)
        lines = text.split("\n")

        # 第一行是日期
        assert lines[0] == digest.date.strftime("%Y-%m-%d")

        # 第二行是空行
        assert lines[1] == ""

        # 后续行是编号条目，从 1 开始
        for i, entry in enumerate(digest.entries, start=1):
            expected_line = f"{i}. {entry.content}"
            assert lines[i + 1] == expected_line



class TestProperty1AppendPreservesContent:
    """
    **Feature: mcp-worklog, Property 1: Append Preserves Existing Content**
    **Validates: Requirements 1.1, 1.3**

    For any existing DailyDigest with N entries, when a new WorkLogEntry is appended,
    the resulting digest SHALL contain all N original entries plus the new entry (N+1 total).
    """

    @settings(max_examples=100)
    @given(
        existing_contents=st.lists(valid_content, min_size=0, max_size=5),
        new_content=valid_content,
    )
    def test_append_preserves_existing_entries(
        self, existing_contents: list[str], new_content: str
    ):
        from mcp_worklog.adapters.outbound.storage import LocalFileStorage
        from mcp_worklog.application import WorklogService

        with tempfile.TemporaryDirectory() as tmp_dir:
            storage = LocalFileStorage(Path(tmp_dir))
            service = WorklogService(storage)

            # 先添加已有条目
            for content in existing_contents:
                service.append_worklog(content)

            # 记录添加前的条目数
            before_count = len(existing_contents)

            # 添加新条目
            result = service.append_worklog(new_content)

            # 验证成功
            assert result.success is True

            # 验证条目数增加 1
            assert result.entry_number == before_count + 1

            # 验证所有原有内容都保留
            digest_result = service.get_daily_digest()
            for original in existing_contents:
                assert original.strip() in digest_result.content



class TestProperty2QueryReturnsStoredContent:
    """
    **Feature: mcp-worklog, Property 2: Query Returns Stored Content**
    **Validates: Requirements 2.2**

    For any date with a stored DailyDigest, calling get_daily_digest with that date
    SHALL return content that matches the stored file content.
    """

    @settings(max_examples=100)
    @given(digest=daily_digest_strategy())
    def test_query_returns_stored_content(self, digest: DailyDigest):
        from mcp_worklog.adapters.outbound.storage import LocalFileStorage
        from mcp_worklog.application import WorklogService

        with tempfile.TemporaryDirectory() as tmp_dir:
            storage = LocalFileStorage(Path(tmp_dir))

            # 直接保存日报
            storage.save(digest)

            # 通过服务查询
            service = WorklogService(storage)
            result = service.get_daily_digest(digest.date)

            # 验证找到
            assert result.found is True

            # 验证日期匹配
            assert result.date == digest.date.strftime("%Y-%m-%d")

            # 验证条目数匹配
            assert result.entry_count == digest.entry_count

            # 验证内容匹配
            expected_content = DigestFormatter.format(digest)
            assert result.content == expected_content



class TestProperty4PolishPreservesNumbering:
    """
    **Feature: mcp-worklog, Property 4: Polish Preserves Entry Count Invariant**
    **Validates: Requirements 5.3, 5.4**

    For any DailyDigest after polishing, the polished content SHALL have
    sequential numbering starting from 1 with no gaps.
    """

    @settings(max_examples=100)
    @given(
        contents=st.lists(valid_content, min_size=1, max_size=10),
    )
    def test_polish_produces_sequential_numbering(self, contents: list[str]):
        import re

        from mcp_worklog.adapters.outbound.storage import LocalFileStorage
        from mcp_worklog.application import WorklogService

        with tempfile.TemporaryDirectory() as tmp_dir:
            storage = LocalFileStorage(Path(tmp_dir))
            service = WorklogService(storage)

            # 添加条目
            for content in contents:
                service.append_worklog(content)

            # 润色
            result = service.polish_digest()

            # 验证成功
            assert result.success is True

            # 验证编号从 1 开始连续
            lines = result.content.split("\n")
            entry_lines = [l for l in lines if re.match(r"^\d+\.", l)]

            for i, line in enumerate(entry_lines, start=1):
                assert line.startswith(f"{i}. "), f"期望编号 {i}，实际: {line}"

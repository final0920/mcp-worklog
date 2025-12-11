"""应用服务 - WorklogService"""

from datetime import date

from mcp_worklog.domain import DailyDigest, DigestFormatter, WorkLogEntry

from .models import AppendResult, DigestResult, PolishResult, RewriteResult, SessionCollectResult
from .ports import StoragePort
from .session_ports import SessionCollectorPort


class WorklogService:
    """工作日志应用服务"""

    def __init__(
        self,
        storage: StoragePort,
        session_collectors: list[SessionCollectorPort] | None = None,
    ) -> None:
        self.storage = storage
        self.session_collectors = session_collectors or []

    def append_worklog(self, summary: str) -> AppendResult:
        """追加工作记录到当天日报"""
        if not summary or not summary.strip():
            return AppendResult(
                success=False,
                file_path="",
                entry_number=0,
                message="工作记录内容不能为空",
            )

        today = date.today()
        digest = self.storage.load(today) or DailyDigest.empty(today)

        entry = WorkLogEntry(content=summary.strip())
        digest.append(entry)

        file_path = self.storage.save(digest)

        return AppendResult(
            success=True,
            file_path=str(file_path),
            entry_number=digest.entry_count,
            message=f"已添加第 {digest.entry_count} 条工作记录",
        )

    def get_daily_digest(self, target_date: date | None = None) -> DigestResult:
        """获取指定日期的日报"""
        target = target_date or date.today()
        digest = self.storage.load(target)

        if digest is None:
            return DigestResult(
                date=target.strftime("%Y-%m-%d"),
                content="",
                entry_count=0,
                found=False,
            )

        content = DigestFormatter.format(digest)
        return DigestResult(
            date=target.strftime("%Y-%m-%d"),
            content=content,
            entry_count=digest.entry_count,
            found=True,
        )

    def polish_digest(self, target_date: date | None = None) -> PolishResult:
        """润色当天日报（基础版本：重新编号）"""
        target = target_date or date.today()
        digest = self.storage.load(target)

        if digest is None:
            return PolishResult(
                success=False,
                date=target.strftime("%Y-%m-%d"),
                content="",
                original_count=0,
                polished_count=0,
            )

        original_count = digest.entry_count

        # 基础润色：去重、重新编号
        seen_contents: set[str] = set()
        unique_entries: list[WorkLogEntry] = []
        for entry in digest.entries:
            normalized = entry.content.strip()
            if normalized not in seen_contents:
                seen_contents.add(normalized)
                unique_entries.append(WorkLogEntry(content=normalized))

        polished_digest = DailyDigest(date=target, entries=unique_entries)
        self.storage.save(polished_digest)

        content = DigestFormatter.format(polished_digest)
        return PolishResult(
            success=True,
            date=target.strftime("%Y-%m-%d"),
            content=content,
            original_count=original_count,
            polished_count=polished_digest.entry_count,
        )

    def collect_sessions(self, target_date: date | None = None) -> SessionCollectResult:
        """采集指定日期的 AI 会话"""
        target = target_date or date.today()
        all_sessions = []

        for collector in self.session_collectors:
            sessions = collector.collect(target)
            all_sessions.extend(sessions)

        # 按时间排序
        all_sessions.sort(key=lambda s: s.start_time)

        return SessionCollectResult(
            date=target.strftime("%Y-%m-%d"),
            sessions=all_sessions,
            total_count=len(all_sessions),
        )

    def rewrite_digest(
        self, target_date: date | None, entries: list[str]
    ) -> RewriteResult:
        """重写日报内容"""
        target = target_date or date.today()

        if not entries:
            return RewriteResult(
                success=False,
                date=target.strftime("%Y-%m-%d"),
                content="",
                entry_count=0,
                message="日报条目不能为空",
            )

        # 创建新的日报
        new_entries = [WorkLogEntry(content=e.strip()) for e in entries if e.strip()]
        new_digest = DailyDigest(date=target, entries=new_entries)
        self.storage.save(new_digest)

        content = DigestFormatter.format(new_digest)
        return RewriteResult(
            success=True,
            date=target.strftime("%Y-%m-%d"),
            content=content,
            entry_count=new_digest.entry_count,
            message="日报已重写",
        )

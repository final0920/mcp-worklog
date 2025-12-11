"""领域服务 - 日报格式化与解析"""

import re
from datetime import date, datetime

from .models import DailyDigest, WorkLogEntry


class DigestFormatter:
    """日报格式化服务"""

    DATE_FORMAT = "%Y-%m-%d"
    ENTRY_PATTERN = re.compile(r"^(\d+)\. (.*)$")

    @staticmethod
    def format(digest: DailyDigest) -> str:
        """格式化日报为简洁编号列表"""
        lines = [digest.date.strftime(DigestFormatter.DATE_FORMAT), ""]

        for i, entry in enumerate(digest.entries, start=1):
            lines.append(f"{i}. {entry.content}")

        return "\n".join(lines)

    @staticmethod
    def parse(text: str, target_date: date) -> DailyDigest:
        """从文本解析日报"""
        entries: list[WorkLogEntry] = []
        lines = text.split("\n")

        for line in lines:
            line = line.lstrip()  # 只去掉行首空格，保留行尾
            if not line.strip():
                continue

            # 跳过日期行
            try:
                datetime.strptime(line.strip(), DigestFormatter.DATE_FORMAT)
                continue
            except ValueError:
                pass

            # 解析编号条目
            match = DigestFormatter.ENTRY_PATTERN.match(line)
            if match:
                content = match.group(2)  # group(2) 是内容部分
                if content.strip():  # 只检查是否有实际内容
                    entries.append(WorkLogEntry(content=content))

        return DailyDigest(date=target_date, entries=entries)

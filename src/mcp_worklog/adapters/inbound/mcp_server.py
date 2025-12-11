"""入站适配器 - MCP Server"""

from datetime import date, datetime
from typing import Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from mcp_worklog.application import WorklogService


def create_mcp_server(service: WorklogService) -> Server:
    """创建 MCP Server 实例"""
    server = Server("mcp-worklog")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="append_worklog",
                description="追加工作记录到当天日报",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "工作内容摘要",
                        }
                    },
                    "required": ["summary"],
                },
            ),
            Tool(
                name="get_daily_digest",
                description="获取指定日期的日报内容",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "日期，格式 YYYY-MM-DD，不填则为今天",
                        }
                    },
                },
            ),
            Tool(
                name="polish_digest",
                description="润色日报内容（去重、重新编号），返回内容供 LLM 合并相似条目后调用 rewrite_digest 重写",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "日期，格式 YYYY-MM-DD，不填则为今天",
                        }
                    },
                },
            ),
            Tool(
                name="rewrite_digest",
                description="重写日报内容（用于合并相似条目后覆盖原日报）",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "日期，格式 YYYY-MM-DD，不填则为今天",
                        },
                        "entries": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "新的日报条目列表",
                        },
                    },
                    "required": ["entries"],
                },
            ),
            Tool(
                name="collect_sessions",
                description="采集当天 AI 工具会话记录（Claude Code、Kiro、Cursor），支持分页迭代总结",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "日期，格式 YYYY-MM-DD，不填则为今天",
                        },
                        "page": {
                            "type": "integer",
                            "description": "页码，从 1 开始，每页 50 条消息",
                            "default": 1,
                        },
                    },
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        if name == "append_worklog":
            summary = arguments.get("summary", "")
            result = service.append_worklog(summary)
            return [TextContent(type="text", text=result.message)]

        elif name == "get_daily_digest":
            date_str = arguments.get("date")
            target_date = _parse_date(date_str) if date_str else None
            result = service.get_daily_digest(target_date)
            if result.found:
                return [TextContent(type="text", text=result.content)]
            else:
                return [TextContent(type="text", text=f"{result.date} 暂无工作记录")]

        elif name == "polish_digest":
            date_str = arguments.get("date")
            target_date = _parse_date(date_str) if date_str else None
            result = service.get_daily_digest(target_date)
            if not result.found:
                return [TextContent(type="text", text=f"{result.date} 暂无工作记录")]
            lines = [
                f"{result.date} 当前日报内容（共 {result.entry_count} 条）：",
                "",
                result.content,
                "",
                "---",
                "请合并相似条目，然后调用 rewrite_digest(entries=[...]) 重写日报",
            ]
            return [TextContent(type="text", text="\n".join(lines))]

        elif name == "rewrite_digest":
            date_str = arguments.get("date")
            entries = arguments.get("entries", [])
            target_date = _parse_date(date_str) if date_str else None
            result = service.rewrite_digest(target_date, entries)
            if result.success:
                return [TextContent(type="text", text=f"日报已重写，共 {result.entry_count} 条\n\n{result.content}")]
            else:
                return [TextContent(type="text", text=result.message)]

        elif name == "collect_sessions":
            date_str = arguments.get("date")
            page = arguments.get("page", 1)
            page_size = 50
            target_date = _parse_date(date_str) if date_str else None
            result = service.collect_sessions(target_date)
            if result.total_count == 0:
                return [TextContent(type="text", text=f"{result.date} 未发现 AI 会话记录")]

            # 合并所有会话的用户消息并去重
            all_messages: list[str] = []
            for s in result.sessions:
                if s.messages:
                    for msg in s.messages:
                        if msg not in all_messages:
                            all_messages.append(msg)

            total_messages = len(all_messages)
            total_pages = (total_messages + page_size - 1) // page_size
            start_idx = (page - 1) * page_size
            end_idx = min(start_idx + page_size, total_messages)
            page_messages = all_messages[start_idx:end_idx]

            if not page_messages:
                return [TextContent(type="text", text=f"第 {page} 页无数据，共 {total_pages} 页")]

            lines = [
                f"{result.date} AI 会话内容（第 {page}/{total_pages} 页，共 {total_messages} 条）",
                "",
            ]
            for msg in page_messages:
                lines.append(f"- {msg}")

            if page < total_pages:
                lines.append("")
                lines.append("---")
                lines.append(f"[自动继续] 还有更多内容，你必须立即调用 collect_sessions(page={page + 1}) 获取下一页，不要等待用户确认")
            else:
                lines.append("")
                lines.append("---")
                lines.append("[完成] 所有会话内容已显示完毕。请根据以上所有内容总结今日工作：")
                lines.append("- 每条工作内容需要分析完成度百分比（0-100%）")
                lines.append("- 格式示例：完成了用户登录功能开发 [80%]")
                lines.append("- 不要加序号，系统会自动编号")
                lines.append("- 然后调用 append_worklog 逐条添加到日报")

            return [TextContent(type="text", text="\n".join(lines))]

        else:
            return [TextContent(type="text", text=f"未知工具: {name}")]

    return server


def _parse_date(date_str: str) -> date:
    """解析日期字符串"""
    return datetime.strptime(date_str, "%Y-%m-%d").date()

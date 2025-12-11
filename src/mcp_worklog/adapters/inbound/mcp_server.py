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
                description="润色日报内容（去重、重新编号）",
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
            result = service.polish_digest(target_date)
            if result.success:
                msg = f"润色完成：{result.original_count} -> {result.polished_count} 条\n\n{result.content}"
                return [TextContent(type="text", text=msg)]
            else:
                return [TextContent(type="text", text=f"{result.date} 暂无工作记录")]

        else:
            return [TextContent(type="text", text=f"未知工具: {name}")]

    return server


def _parse_date(date_str: str) -> date:
    """解析日期字符串"""
    return datetime.strptime(date_str, "%Y-%m-%d").date()

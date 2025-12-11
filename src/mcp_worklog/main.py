"""MCP Worklog 入口点"""

import argparse
import asyncio
from pathlib import Path

from mcp.server.stdio import stdio_server

from mcp_worklog.adapters.inbound.mcp_server import create_mcp_server
from mcp_worklog.adapters.outbound.storage import LocalFileStorage
from mcp_worklog.application import WorklogService


async def run_server(storage_path: Path) -> None:
    """运行 MCP Server"""
    storage = LocalFileStorage(storage_path)
    service = WorklogService(storage)
    server = create_mcp_server(service)

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main() -> None:
    """主入口"""
    parser = argparse.ArgumentParser(description="MCP Worklog Server")
    parser.add_argument(
        "--storage-path",
        type=str,
        required=True,
        help="日报存储目录路径",
    )
    args = parser.parse_args()

    storage_path = Path(args.storage_path).expanduser()
    asyncio.run(run_server(storage_path))


if __name__ == "__main__":
    main()

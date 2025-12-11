# MCP Worklog

MCP 服务：自动化生成和管理工作日报，支持从 AI 工具会话中采集内容。

## 功能

- 追加工作记录到当天日报
- 查询指定日期的日报内容
- 润色和整理日报内容
- 采集 AI 工具会话记录（Claude Code、Kiro、Cursor）
- 重写日报内容（合并相似条目）

## 安装

```bash
pip install mcp-worklog
```

## 配置

```json
{
  "mcpServers": {
    "worklog": {
      "command": "python",
      "args": ["-m", "mcp_worklog.main", "--storage-path", "/path/to/worklogs"],
      "autoApprove": ["append_worklog", "get_daily_digest", "polish_digest", "collect_sessions", "rewrite_digest"]
    }
  }
}
```

conda 环境需指定完整路径：

```json
{
  "command": "/path/to/conda/envs/your_env/python"
}
```

## 工具

| 工具名 | 描述 |
|--------|------|
| `append_worklog` | 追加工作记录到当天日报 |
| `get_daily_digest` | 获取指定日期的日报内容 |
| `polish_digest` | 获取日报内容供 LLM 合并相似条目 |
| `collect_sessions` | 采集 AI 会话记录（支持分页） |
| `rewrite_digest` | 重写日报内容 |

## 会话采集

支持采集以下 AI 工具的会话记录：
- Claude Code (`~/.claude/projects/`)
- Kiro (`%APPDATA%/Kiro/User/globalStorage/kiro.kiroagent/`)
- Cursor (`%APPDATA%/Cursor/User/workspaceStorage/`)

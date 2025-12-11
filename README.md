# MCP Worklog

MCP 服务：自动化生成和管理工作日报。

## 功能

- 追加工作记录到当天日报
- 查询指定日期的日报内容
- 润色和整理日报内容（去重、重新编号）

## 安装

```bash
pip install mcp-worklog
```

## 配置

在 MCP 客户端配置文件中添加：

```json
{
  "mcpServers": {
    "worklog": {
      "command": "python",
      "args": ["-m", "mcp_worklog.main", "--storage-path", "/path/to/worklogs"],
      "autoApprove": ["append_worklog", "get_daily_digest", "polish_digest"]
    }
  }
}
```

如果使用 conda 环境，需指定 Python 解释器完整路径：

```json
{
  "mcpServers": {
    "worklog": {
      "command": "/path/to/conda/envs/your_env/python",
      "args": ["-m", "mcp_worklog.main", "--storage-path", "/path/to/worklogs"]
    }
  }
}
```

## 工具

| 工具名 | 描述 |
|--------|------|
| `append_worklog` | 追加工作记录到当天日报 |
| `get_daily_digest` | 获取指定日期的日报内容 |
| `polish_digest` | 润色日报（去重、重新编号） |

## 日报格式

```
2024-12-11

1. 完成用户认证模块开发
2. 修复数据导出性能问题
3. 评审新功能设计方案
```

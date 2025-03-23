# Project2Github

一键将本地目录创建为GitHub仓库的工具。支持Windows、Linux和macOS平台。

## 功能特点

- 自动初始化本地Git仓库
- 自动创建GitHub远程仓库
- 自动推送代码到GitHub
- 支持创建私有仓库
- 跨平台支持

## 安装要求

- Python 3.8+
- Git

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

1. 创建GitHub个人访问令牌（Personal Access Token）:
   - 访问 GitHub Settings -> Developer settings -> Personal access tokens
   - 生成新token，确保勾选`repo`权限

2. 创建`.env`文件，添加你的GitHub Token：
```
GITHUB_TOKEN=your_github_token_here
```

## 使用方法

基本用法：
```bash
python project2github.py /path/to/your/project
```

创建私有仓库：
```bash
python project2github.py /path/to/your/project --private
```

指定仓库名称：
```bash
python project2github.py /path/to/your/project --name custom_repo_name
```

## 参数说明

- `directory`: 要上传的本地目录路径（必需）
- `--name`: GitHub仓库名称（可选，默认使用目录名）
- `--private`: 创建私有仓库（可选，默认为公开仓库）

## MCP Server Integration

This project now includes an MCP (Model Context Protocol) server implementation, allowing AI systems to interact with it via stdio.

### MCP Server Usage

1. Start the MCP server:
```bash
python server.py
```

2. The server supports the following MCP operations:
   - `create_repo`: Create a new GitHub repository
   
   Note: The `list_repos` and `delete_repo` operations are not yet implemented

3. Example MCP request:
```json
{
  "operation": "create_repo",
  "params": {
    "directory": "/path/to/project",
    "name": "my-repo",
    "private": true
  }
}
```

## 许可证

MIT

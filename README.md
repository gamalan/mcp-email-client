# Mail Client MCP

## Overview

Mail Client MCP is a Python-based email client that allows users to manage email configurations, send emails, and read the latest unread emails. It provide MCP for Claude Desktop

## Features

- List all email configurations
- Add new email configurations
- Update existing email configurations
- Delete email configurations
- Send emails using specified configurations
- Read the latest 5 unread emails

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/gamalan/mcp-email-client.git
    cd mcp-email-client
    ```
2. Install uv
    Linux/MacOS
    ```sh
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
    Windows
    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

3. Install dependencies:
    ```sh
    uv sync
    ```

## Configuration

Configuration example using Claude Desktop
```json
{
  "mcpServers": {
    "mcp_email_client": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "D:\\Project\\RepoPath", 
        "mcp_email_client"
      ]
    }
  }
}
```

or in VsCode

```json
{
    "servers": {
        "any-name": {
            "type": "stdio",
            "command": "/path/to/uv",
            "args": [
                "run",
                "--directory",
                "/path/to/repo",
                "run_mcp_server.py",
            ]
        }
    }
}
```
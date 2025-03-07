import asyncio
import logging
from pathlib import Path
from typing import Sequence
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
)
from .mailhandler import *


async def serve() -> Server:
    logger = logging.getLogger(__name__)
    server = Server("EmailClient")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="list_email_configs",
                description="List all email configurations",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "command": {"type": "string"},
                    },
                    "required": [""],
                }
            ),
            Tool(
                name="update_email_config",
                description="Update email configuration",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "imap_email": {"type": "string"},
                        "imap_password": {"type": "string"},
                        "imap_server": {"type": "string"},
                        "imap_port": {"type": "integer"},
                        "imap_ssl": {"type": "boolean"},
                        "is_server_same": {"type": "boolean"},
                        "smtp_email": {"type": "string"},
                        "smtp_password": {"type": "string"},
                        "smtp_server": {"type": "string"},
                        "smtp_port": {"type": "integer"},
                        "smtp_ssl": {"type": "string"},
                    },
                    "required": ["name", "imap_email", "imap_password", "imap_server", "imap_port", "imap_ssl", "is_server_same"],
                }
            ),
            Tool(
                name="delete_email_config",
                description="Delete email configuration",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                    },
                    "required": ["name"],
                }
            ),
            Tool(
                name="send_email",
                description="Send an email",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "subject": {"type": "string"},
                        "body": {"type": "string"},
                        "to": {"type": "string"},
                        "cc": {"type": "string"},
                        "bcc": {"type": "string"},
                    },
                    "required": ["name", "subject", "body", "to"],
                }
            ),
            Tool(
                name="read_email",
                description="Read latest 5 unread emails",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                    },
                    "required": ["name"],
                }
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        if name == "list_email_configs":
            list_config = handleListConfigs()
            return [TextContent(type="text",text=f'Email configs:{list_config}')]
        elif name == "add_email_config":
            add_config = handleAddConfig(name,**arguments)
            return [TextContent(type="text",text=f'Email config added:{add_config}')]
        elif name == "update_email_config":
            update_config = handleUpdateConfig(name,**arguments)
            return [TextContent(type="text",text=f'Email config updated:{update_config}')]
        elif name == "delete_email_config":
            delete_config = handleDeleteConfig(name)
            return [TextContent(type="text",text=f'Email config deleted:{delete_config}')]
        elif name == "send_email":
            send_email = handleSendEmail(name,**arguments)
            return [TextContent(type="text",text=f'Email sent:{send_email}')]
        elif name == "read_email":
            read_emails = handleLoadFiveLatestEmails(name)
            return [TextContent(type="text",text=f'Email received:{read_emails}')]
        else:
            raise ValueError(f"Unknown tool: {name}")

    return server


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    async def _run():
        server = await serve()
        options = server.create_initialization_options()
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, options, raise_exceptions=True)
    asyncio.run(_run())
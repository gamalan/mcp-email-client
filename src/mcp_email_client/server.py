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
                name="add_email_config",
                description="Add email configuration",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "_name": {"type": "string"},
                        "inbound_user": {"type": "string"},
                        "inbound_password": {"type": "string"},
                        "inbound_host": {"type": "string"},
                        "inbound_port": {"type": "integer"},
                        "inbound_ssl": {"type": "boolean"},
                        "is_outbound_equal": {"type": "boolean"},
                        "outbound_user": {"type": "string"},
                        "outbound_password": {"type": "string"},
                        "outbound_host": {"type": "string"},
                        "outbound_port": {"type": "integer"},
                        "outbound_ssl": {"type": "string"},
                    },
                    "required": ["_name", "inbound_user", "inbound_password", "inbound_host", "inbound_port", "inbound_ssl", "is_outbound_equal"],
                }
            ),
            Tool(
                name="update_email_config",
                description="Update email configuration",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "_name": {"type": "string"},
                        "inbound_user": {"type": "string"},
                        "inbound_password": {"type": "string"},
                        "inbound_host": {"type": "string"},
                        "inbound_port": {"type": "integer"},
                        "inbound_ssl": {"type": "boolean"},
                        "is_outbound_equal": {"type": "boolean"},
                        "outbound_user": {"type": "string"},
                        "outbound_password": {"type": "string"},
                        "outbound_host": {"type": "string"},
                        "outbound_port": {"type": "integer"},
                        "outbound_ssl": {"type": "string"},
                    },
                    "required": ["_name", "inbound_user", "inbound_password", "inbound_host", "inbound_port", "inbound_ssl", "is_outbound_equal"],
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
            add_config = handleAddConfig(**arguments)
            return [TextContent(type="text",text=f'Email config added:{add_config}')]
        elif name == "update_email_config":
            config_name = arguments['_name']
            del arguments['_name']
            update_config = handleUpdateConfig(config_name,**arguments)
            return [TextContent(type="text",text=f'Email config updated:{update_config}')]
        elif name == "delete_email_config":
            delete_config = handleDeleteConfig(arguments['name'])
            return [TextContent(type="text",text=f'Email config deleted:{delete_config}')]
        elif name == "send_email":
            config_name = arguments['_name']
            del arguments['_name']
            send_email = handleSendEmail(config_name,**arguments)
            return [TextContent(type="text",text=f'Email sent:{send_email}')]
        elif name == "read_email":
            config_name = arguments['_name']
            del arguments['_name']
            read_emails = handleLoadFiveLatestEmails(config_name)
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
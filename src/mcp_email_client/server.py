import asyncio
import logging
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
)
from mcp_email_client.mailhandler import (
    handleAddConfig, 
    handleUpdateConfig, 
    handleDeleteConfig, 
    handleListConfigs, 
    handleSendEmail, 
    handleLoadHundredLatestEmails, 
    handleSearchEmails,
    handleLoadEmailsByDateRange,
    handleLoadAllEmails,
    handleGetEmailCount,
    handleSemanticSearchEmails,
    handleGenerateEmbeddings
)

async def serve(repository: Path | None) -> None:
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
                description="Add a new email configuration",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "inbound_user": {"type": "string"},
                        "inbound_password": {"type": "string"},
                        "inbound_host": {"type": "string"},
                        "inbound_port": {"type": "integer"},
                        "inbound_ssl": {"type": "string"},
                        "is_outbound_equal": {"type": "boolean"},
                        "outbound_user": {"type": "string"},
                        "outbound_password": {"type": "string"},
                        "outbound_host": {"type": "string"},
                        "outbound_port": {"type": "integer"},
                        "outbound_ssl": {"type": "string"},
                    },
                    "required": ["name", "inbound_user", "inbound_password", "inbound_host", "inbound_port", "inbound_ssl", "is_outbound_equal"],
                }
            ),
            Tool(
                name="update_email_config",
                description="Update email configuration",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "inbound_user": {"type": "string"},
                        "inbound_password": {"type": "string"},
                        "inbound_host": {"type": "string"},
                        "inbound_port": {"type": "integer"},
                        "inbound_ssl": {"type": "string"},
                        "is_outbound_equal": {"type": "boolean"},
                        "outbound_user": {"type": "string"},
                        "outbound_password": {"type": "string"},
                        "outbound_host": {"type": "string"},
                        "outbound_port": {"type": "integer"},
                        "outbound_ssl": {"type": "string"},
                    },
                    "required": ["name", "inbound_user", "inbound_password", "inbound_host", "inbound_port", "inbound_ssl", "is_outbound_equal"],
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
            Tool(
                name="search_emails",
                description="Search emails by content",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Email configuration name (optional)"},
                        "query": {"type": "string", "description": "Search query text"},
                        "limit": {"type": "integer", "description": "Maximum number of results (default: 10)"},
                    },
                    "required": ["query"],
                }
            ),
            Tool(
                name="get_emails_by_date",
                description="Get emails within a date range",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Email configuration name"},
                        "start_date": {"type": "string", "description": "Start date in ISO format (YYYY-MM-DD)"},
                        "end_date": {"type": "string", "description": "End date in ISO format (YYYY-MM-DD), defaults to today if not provided"},
                        "limit": {"type": "integer", "description": "Maximum number of results (default: 100)"},
                    },
                    "required": ["name", "start_date"],
                }
            ),
            Tool(
                name="get_all_emails",
                description="Get all emails from the database",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Email configuration name (optional)"},
                        "limit": {"type": "integer", "description": "Maximum number of results (default: 1000)"},
                    },
                    "required": [],
                }
            ),
            Tool(
                name="get_email_count",
                description="Get the total count of emails in the database",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Email configuration name (optional)"},
                    },
                    "required": [],
                }
            ),
            Tool(
                name="semantic_search_emails",
                description="Search emails using semantic similarity",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query text"},
                        "name": {"type": "string", "description": "Email configuration name (optional)"},
                        "similarity_threshold": {"type": "number", "description": "Minimum similarity score (0-1) to include in results (default: 0.6)"},
                        "limit": {"type": "integer", "description": "Maximum number of results (default: 10)"},
                    },
                    "required": ["query"],
                }
            ),
            Tool(
                name="generate_embeddings",
                description="Generate embeddings for all emails that don't have them yet",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "batch_size": {"type": "integer", "description": "Number of emails to process in each batch (default: 100)"},
                    },
                    "required": [],
                }
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        if name == "list_email_configs":
            list_config = handleListConfigs()
            return [TextContent(type="text",text=f'Email configs:{list_config}')]
        elif name == "add_email_config":
            config_name = arguments.get("name")
            del arguments["name"]
            add_config = handleAddConfig(config_name, **arguments)
            return [TextContent(type="text",text=f'Email config added:{add_config}')]
        elif name == "update_email_config":
            config_name = arguments.get("name")
            del arguments["name"]
            update_config = handleUpdateConfig(config_name, **arguments)
            return [TextContent(type="text",text=f'Email config updated:{update_config}')]
        elif name == "delete_email_config":
            config_name = arguments.get("name")
            delete_config = handleDeleteConfig(config_name)
            return [TextContent(type="text",text=f'Email config deleted:{delete_config}')]
        elif name == "send_email":
            config_name = arguments.get("name")
            send_email = handleSendEmail(
                config_name=config_name,
                subject=arguments.get("subject"),
                body=arguments.get("body"),
                to=arguments.get("to"),
                cc=arguments.get("cc"),
                bcc=arguments.get("bcc")
            )
            return [TextContent(type="text",text=f'Email sent:{send_email}')]
        elif name == "read_email":
            config_name = arguments.get("name")
            read_emails = handleLoadHundredLatestEmails(config_name)
            return [TextContent(type="text",text=f'Email received:{read_emails}')]
        elif name == "search_emails":
            config_name = arguments.get("name")  # Optional
            query = arguments.get("query")
            limit = arguments.get("limit", 10)
            search_results = handleSearchEmails(config_name, query, limit)
            return [TextContent(type="text",text=f'Search results:{search_results}')]
        elif name == "get_emails_by_date":
            config_name = arguments.get("name")
            start_date = arguments.get("start_date")
            end_date = arguments.get("end_date")
            limit = arguments.get("limit", 100)
            results = handleLoadEmailsByDateRange(config_name, start_date, end_date, limit)
            return [TextContent(type="text",text=f'Emails by date range:{results}')]
        elif name == "get_all_emails":
            config_name = arguments.get("name")
            limit = arguments.get("limit", 1000)
            results = handleLoadAllEmails(config_name, limit)
            return [TextContent(type="text",text=f'All emails:{results}')]
        elif name == "get_email_count":
            config_name = arguments.get("name")
            count = handleGetEmailCount(config_name)
            return [TextContent(type="text",text=f'Email count:{count}')]
        elif name == "semantic_search_emails":
            query = arguments.get("query")
            config_name = arguments.get("name")
            similarity_threshold = arguments.get("similarity_threshold", 0.6)
            limit = arguments.get("limit", 10)
            search_results = handleSemanticSearchEmails(
                query=query,
                config_name=config_name,
                similarity_threshold=similarity_threshold,
                limit=limit
            )
            return [TextContent(type="text",text=f'Semantic search results:{search_results}')]
        elif name == "generate_embeddings":
            batch_size = arguments.get("batch_size", 100)
            stats = handleGenerateEmbeddings(batch_size=batch_size)
            return [TextContent(type="text",text=f'Embedding generation stats:{stats}')]
        else:
            raise ValueError(f"Unknown tool: {name}")

    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options, raise_exceptions=True)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    async def _run():
        server = await serve()
        options = server.create_initialization_options()
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, options, raise_exceptions=True)
    asyncio.run(_run())
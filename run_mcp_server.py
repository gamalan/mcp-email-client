#!/usr/bin/env python3
"""
MCP Server Launcher for testing

This script starts the MCP server for interactive testing.
Run it from VS Code to test the MCP server functionality.
"""
import asyncio
import logging
import sys
from pathlib import Path
import os

# Add the current directory to the path to ensure modules can be found
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from mcp_email_client.server import serve

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def main():
    try:
        logger.info("Starting MCP Email server...")
        
        # Get the current directory as the repository path
        repo_path = Path(os.path.dirname(os.path.abspath(__file__)))
        
        # Run the server
        await serve(repo_path)
    except Exception as e:
        logger.error(f"Error starting MCP server: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
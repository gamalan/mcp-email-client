import sys
import os
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
import json
import asyncio

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import with mocks to avoid actual connections and model loading
with patch('smtplib.SMTP_SSL'), patch('smtplib.SMTP'), \
     patch('imaplib.IMAP4_SSL'), patch('imaplib.IMAP4'), \
     patch('sentence_transformers.SentenceTransformer'):
    import mailclient
    from mailclient import serve
    import mail
    from mail import (
        handleListConfigs,
        handleSendEmail,
        handleSearchEmails,
        handleLoadEmailsByDateRange
    )
    from config import MailConfig

class TestMCPServer(unittest.TestCase):
    """Test MCP server functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock all the handler functions
        self.patcher_list_configs = patch('mailclient.handleListConfigs')
        self.mock_list_configs = self.patcher_list_configs.start()
        self.mock_list_configs.return_value = ["test_config"]
        
        self.patcher_send_email = patch('mailclient.handleSendEmail')
        self.mock_send_email = self.patcher_send_email.start()
        self.mock_send_email.return_value = "Email sent successfully."
        
        self.patcher_search_emails = patch('mailclient.handleSearchEmails')
        self.mock_search_emails = self.patcher_search_emails.start()
        self.mock_search_emails.return_value = [
            {'id': 1, 'subject': 'Test Email', 'body': 'Test Body'}
        ]
        
        self.patcher_load_emails_by_date = patch('mailclient.handleLoadEmailsByDateRange')
        self.mock_load_emails_by_date = self.patcher_load_emails_by_date.start()
        self.mock_load_emails_by_date.return_value = [
            {'id': 1, 'subject': 'Test Email', 'date': '2025-04-15 12:00:00'}
        ]
        
        # Mock the Server class and its methods
        self.patcher_server = patch('mcp.server.Server')
        self.mock_server_class = self.patcher_server.start()
        
        self.mock_server = MagicMock()
        self.mock_server.list_tools = MagicMock()
        self.mock_server.list_tools.return_value = lambda f: f
        self.mock_server.call_tool = MagicMock()
        self.mock_server.call_tool.return_value = lambda f: f
        
        self.mock_server.create_initialization_options = MagicMock()
        self.mock_server.create_initialization_options.return_value = {}
        
        self.mock_server.run = AsyncMock()
        
        self.mock_server_class.return_value = self.mock_server
    
    def tearDown(self):
        """Clean up after tests."""
        self.patcher_list_configs.stop()
        self.patcher_send_email.stop()
        self.patcher_search_emails.stop()
        self.patcher_load_emails_by_date.stop()
        self.patcher_server.stop()
    
    @patch('mailclient.stdio_server')
    async def test_server_initialization(self, mock_stdio):
        """Test the server initialization."""
        # Setup mock for stdio_server context manager
        mock_cm = AsyncMock()
        mock_stdio.return_value = mock_cm
        mock_cm.__aenter__.return_value = (AsyncMock(), AsyncMock())
        
        # Call serve function
        await serve(None)
        
        # Verify Server was created with correct name
        self.mock_server_class.assert_called_once_with("EmailClient")
        
        # Verify stdio_server was used
        mock_stdio.assert_called_once()
        
        # Verify server.run was called
        self.mock_server.run.assert_called_once()

    async def test_list_tools(self):
        """Test the list_tools handler."""
        # Get the list_tools function
        list_tools_decorator = self.mock_server.list_tools
        list_tools_func = list_tools_decorator.call_args[0][0]
        
        # Call the function
        tools = await list_tools_func()
        
        # Verify tools list contains expected tools
        tool_names = [tool.name for tool in tools]
        self.assertIn("list_email_configs", tool_names)
        self.assertIn("send_email", tool_names)
        self.assertIn("search_emails", tool_names)
        self.assertIn("semantic_search_emails", tool_names)
        
        # Check the schema for a specific tool
        send_email_tool = next(tool for tool in tools if tool.name == "send_email")
        self.assertEqual(send_email_tool.description, "Send an email")
        self.assertIn("subject", send_email_tool.inputSchema["properties"])
        self.assertIn("body", send_email_tool.inputSchema["properties"])
        self.assertIn("to", send_email_tool.inputSchema["properties"])
    
    async def test_call_tool_list_configs(self):
        """Test calling the list_email_configs tool."""
        # Get the call_tool function
        call_tool_decorator = self.mock_server.call_tool
        call_tool_func = call_tool_decorator.call_args[0][0]
        
        # Call the function with list_email_configs
        result = await call_tool_func("list_email_configs", {})
        
        # Verify the handler was called
        self.mock_list_configs.assert_called_once()
        
        # Verify result format
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].type, "text")
        self.assertIn("Email configs", result[0].text)
    
    async def test_call_tool_send_email(self):
        """Test calling the send_email tool."""
        # Get the call_tool function
        call_tool_decorator = self.mock_server.call_tool
        call_tool_func = call_tool_decorator.call_args[0][0]
        
        # Call the function with send_email
        args = {
            "name": "test_config",
            "subject": "Test Subject",
            "body": "Test Body",
            "to": "recipient@example.com"
        }
        result = await call_tool_func("send_email", args)
        
        # Verify the handler was called with right args
        self.mock_send_email.assert_called_once()
        call_args, call_kwargs = self.mock_send_email.call_args
        self.assertEqual(call_kwargs["name"], "test_config")
        self.assertEqual(call_kwargs["subject"], "Test Subject")
        self.assertEqual(call_kwargs["body"], "Test Body")
        self.assertEqual(call_kwargs["to"], "recipient@example.com")
        
        # Verify result format
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].type, "text")
        self.assertIn("Email sent", result[0].text)
    
    async def test_call_tool_unknown(self):
        """Test calling an unknown tool."""
        # Get the call_tool function
        call_tool_decorator = self.mock_server.call_tool
        call_tool_func = call_tool_decorator.call_args[0][0]
        
        # Call with unknown tool name
        with self.assertRaises(ValueError) as context:
            await call_tool_func("unknown_tool", {})
        
        # Verify error message
        self.assertIn("Unknown tool", str(context.exception))


if __name__ == "__main__":
    # Run the tests with asyncio support
    loop = asyncio.get_event_loop()
    unittest.main()
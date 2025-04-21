import sys
import os
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import datetime

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import with mocks to avoid actual SMTP/IMAP connections
with patch('smtplib.SMTP_SSL'), patch('smtplib.SMTP'), patch('imaplib.IMAP4_SSL'), patch('imaplib.IMAP4'):
    from mail import (
        handleSendEmail, 
        handleLoadFiveLatestEmails,
        handleLoadEmailsByDateRange,
        handleLoadAllEmails,
        handleSearchEmails,
        handleSemanticSearchEmails
    )
    from config import MailConfig

class TestMailFunctions(unittest.TestCase):
    """Test mail module functions."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock the database functions
        self.patcher1 = patch('mail.insert_email')
        self.mock_insert_email = self.patcher1.start()
        self.mock_insert_email.return_value = 1  # Return a fake email ID
        
        self.patcher2 = patch('mail.get_emails')
        self.mock_get_emails = self.patcher2.start()
        
        self.patcher3 = patch('mail.search_emails_by_content')
        self.mock_search_emails = self.patcher3.start()
        
        self.patcher4 = patch('mail.get_emails_by_date_range')
        self.mock_get_emails_by_date = self.patcher4.start()
        
        self.patcher5 = patch('mail.get_all_emails')
        self.mock_get_all_emails = self.patcher5.start()
        
        self.patcher6 = patch('mail.semantic_search')
        self.mock_semantic_search = self.patcher6.start()
        
        self.patcher7 = patch('mail.update_email_with_embedding')
        self.mock_update_with_embedding = self.patcher7.start()
        
        # Mock the MailConfig class
        self.patcher_config = patch('mail.MailConfig')
        self.mock_config_class = self.patcher_config.start()
        
        # Create a mock config
        self.mock_config = MagicMock()
        self.mock_config.outbound_ssl = "SSL/TLS"
        self.mock_config.outbound_host = "smtp.example.com"
        self.mock_config.outbound_port = 465
        self.mock_config.outbound_user = "user@example.com"
        self.mock_config.outbound_password = "password"
        self.mock_config.inbound_ssl = "SSL/TLS"
        self.mock_config.inbound_host = "imap.example.com"
        self.mock_config.inbound_port = 993
        self.mock_config.inbound_user = "user@example.com"
        self.mock_config.inbound_password = "password"
        
        # Set up the load_entry method to return our mock config
        self.mock_config_class.load_entry.return_value = self.mock_config
    
    def tearDown(self):
        """Clean up after tests."""
        self.patcher1.stop()
        self.patcher2.stop()
        self.patcher3.stop()
        self.patcher4.stop()
        self.patcher5.stop()
        self.patcher6.stop()
        self.patcher7.stop()
        self.patcher_config.stop()
    
    def test_handle_send_email(self):
        """Test sending an email."""
        # Mock the SMTP server
        with patch('smtplib.SMTP_SSL') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value = mock_server
            
            # Call the function to send an email
            result = handleSendEmail(
                config_name="test_config",
                subject="Test Subject",
                body="Test Body",
                to="recipient@example.com",
                cc="cc@example.com",
                bcc="bcc@example.com"
            )
            
            # Verify SMTP methods were called correctly
            mock_server.login.assert_called_once_with("user@example.com", "password")
            mock_server.sendmail.assert_called_once()
            mock_server.quit.assert_called_once()
            
            # Verify email was inserted into database
            self.mock_insert_email.assert_called_once_with(
                config_name="test_config",
                subject="Test Subject",
                body="Test Body",
                sender="user@example.com",
                recipients="recipient@example.com",
                cc="cc@example.com",
                bcc="bcc@example.com",
                raw_content=mock_server.sendmail.call_args[0][2]
            )
            
            # Verify embedding was generated and stored
            self.mock_update_with_embedding.assert_called_once_with(1, "Test Subject Test Body")
            
            # Verify function returned success message
            self.assertEqual(result, "Email sent successfully.")
    
    def test_handle_search_emails(self):
        """Test searching emails by content."""
        # Setup mock search results
        mock_results = [
            {'id': 1, 'subject': 'Email 1', 'body': 'Body 1'},
            {'id': 2, 'subject': 'Email 2', 'body': 'Body 2'}
        ]
        self.mock_search_emails.return_value = mock_results
        
        # Call the search function
        result = handleSearchEmails(
            config_name="test_config",
            query="search term",
            limit=10
        )
        
        # Verify search function was called correctly
        self.mock_search_emails.assert_called_once_with("search term", "test_config", 10)
        
        # Verify function returned the search results
        self.assertEqual(result, mock_results)
    
    def test_handle_semantic_search_emails(self):
        """Test semantic search for emails."""
        # Setup mock semantic search results with similarity scores
        mock_results = [
            {'id': 1, 'subject': 'Email 1', 'body': 'Body 1', 'similarity_score': 0.95},
            {'id': 2, 'subject': 'Email 2', 'body': 'Body 2', 'similarity_score': 0.75}
        ]
        self.mock_semantic_search.return_value = mock_results
        
        # Call the semantic search function
        result = handleSemanticSearchEmails(
            query="search term",
            config_name="test_config",
            similarity_threshold=0.7,
            limit=10
        )
        
        # Verify semantic search function was called correctly
        self.mock_semantic_search.assert_called_once_with(
            query="search term",
            config_name="test_config",
            similarity_threshold=0.7,
            limit=10
        )
        
        # Verify function returned the semantic search results
        self.assertEqual(result, mock_results)
    
    def test_handle_load_emails_by_date_range(self):
        """Test loading emails by date range."""
        # Setup mock date range results
        test_date = datetime.datetime(2025, 4, 1)
        mock_results = [
            {'id': 1, 'subject': 'Email 1', 'date': test_date},
            {'id': 2, 'subject': 'Email 2', 'date': test_date}
        ]
        self.mock_get_emails_by_date.return_value = mock_results
        
        # Call the function to get emails by date range
        result = handleLoadEmailsByDateRange(
            config_name="test_config",
            start_date="2025-04-01",
            end_date="2025-04-15",
            limit=100
        )
        
        # Verify the date range function was called with correct parameters
        self.mock_get_emails_by_date.assert_called_once()
        args, kwargs = self.mock_get_emails_by_date.call_args
        self.assertEqual(kwargs['config_name'], "test_config")
        self.assertEqual(kwargs['limit'], 100)
        
        # Verify function returned the correct results
        self.assertEqual(result, mock_results)

if __name__ == "__main__":
    unittest.main()
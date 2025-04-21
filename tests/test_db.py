import sys
import os
import unittest
import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import mcp_email_client.db as db

class TestDatabaseOperations(unittest.TestCase):
    """Test database operations in the db module."""
    
    def setUp(self):
        """Set up test environment."""
        # Use a test database file
        self.original_db_file = db.DB_FILE
        db.DB_FILE = Path("test_emails.duckdb")
        db.init_db()
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove test database
        if Path("test_emails.duckdb").exists():
            os.remove("test_emails.duckdb")
        # Restore original DB file
        db.DB_FILE = self.original_db_file
    
    def test_insert_and_get_email(self):
        """Test inserting and retrieving an email."""
        # Insert test email
        email_id = db.insert_email(
            config_name="test_config",
            subject="Test Subject",
            body="Test Body",
            sender="sender@example.com",
            recipients="recipient@example.com",
            cc="cc@example.com",
            bcc="bcc@example.com"
        )
        
        # Verify email was inserted and has an ID
        self.assertIsNotNone(email_id)
        
        # Retrieve the email
        emails = db.get_emails(config_name="test_config")
        
        # Verify email was retrieved correctly
        self.assertEqual(len(emails), 1)
        self.assertEqual(emails[0]['subject'], "Test Subject")
        self.assertEqual(emails[0]['body'], "Test Body")
        self.assertEqual(emails[0]['sender'], "sender@example.com")
        self.assertEqual(emails[0]['recipients'], "recipient@example.com")
        self.assertEqual(emails[0]['cc'], "cc@example.com")
        self.assertEqual(emails[0]['bcc'], "bcc@example.com")
    
    def test_get_emails_by_date_range(self):
        """Test retrieving emails within a date range."""
        # Insert test emails with different dates
        past_date = datetime.datetime.now() - datetime.timedelta(days=10)
        recent_date = datetime.datetime.now() - datetime.timedelta(days=2)
        
        # Email from 10 days ago
        db.insert_email(
            config_name="test_config",
            subject="Old Email",
            body="Old Body",
            sender="old@example.com",
            recipients="recipient@example.com",
            date=past_date
        )
        
        # Email from 2 days ago
        db.insert_email(
            config_name="test_config",
            subject="Recent Email",
            body="Recent Body",
            sender="recent@example.com",
            recipients="recipient@example.com",
            date=recent_date
        )
        
        # Get emails from the last 5 days
        start_date = datetime.datetime.now() - datetime.timedelta(days=5)
        emails = db.get_emails_by_date_range(
            start_date=start_date,
            config_name="test_config"
        )
        
        # Should only get the recent email
        self.assertEqual(len(emails), 1)
        self.assertEqual(emails[0]['subject'], "Recent Email")
        
        # Get all emails
        all_emails = db.get_emails_by_date_range(
            start_date=past_date - datetime.timedelta(days=1),
            config_name="test_config"
        )
        
        # Should get both emails
        self.assertEqual(len(all_emails), 2)
    
    def test_search_emails_by_content(self):
        """Test searching emails by content."""
        # Insert test emails with different content
        db.insert_email(
            config_name="test_config",
            subject="Meeting Agenda",
            body="We will discuss the new project timeline.",
            sender="manager@example.com",
            recipients="team@example.com"
        )
        
        db.insert_email(
            config_name="test_config",
            subject="Project Update",
            body="The timeline has been extended by two weeks.",
            sender="manager@example.com",
            recipients="team@example.com"
        )
        
        # Search for "timeline"
        results = db.search_emails_by_content("timeline", "test_config")
        
        # Should find both emails
        self.assertEqual(len(results), 2)
        
        # Search for "project"
        results = db.search_emails_by_content("project", "test_config")
        
        # Should find both emails
        self.assertEqual(len(results), 2)
        
        # Search for "meeting"
        results = db.search_emails_by_content("meeting", "test_config")
        
        # Should find only the meeting email
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['subject'], "Meeting Agenda")
        
        # Search for "extended"
        results = db.search_emails_by_content("extended", "test_config")
        
        # Should find only the update email
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['subject'], "Project Update")
        
    def test_email_count(self):
        """Test counting emails in the database."""
        # Insert test emails
        db.insert_email(
            config_name="test_config1",
            subject="Email 1",
            body="Body 1",
            sender="sender1@example.com",
            recipients="recipient@example.com"
        )
        
        db.insert_email(
            config_name="test_config1",
            subject="Email 2",
            body="Body 2",
            sender="sender2@example.com",
            recipients="recipient@example.com"
        )
        
        db.insert_email(
            config_name="test_config2",
            subject="Email 3",
            body="Body 3",
            sender="sender3@example.com",
            recipients="recipient@example.com"
        )
        
        # Count all emails
        count = db.get_email_count()
        self.assertEqual(count, 3)
        
        # Count emails for test_config1
        count = db.get_email_count(config_name="test_config1")
        self.assertEqual(count, 2)
        
        # Count emails for test_config2
        count = db.get_email_count(config_name="test_config2")
        self.assertEqual(count, 1)

if __name__ == "__main__":
    unittest.main()
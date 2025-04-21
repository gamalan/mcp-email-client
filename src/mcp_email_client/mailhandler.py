from .config import MailConfig
import smtplib, imaplib, email
import logging
from imapclient import IMAPClient

logger = logging.getLogger(__name__)

def handleAddConfig(**kwargs):
    try:
        config = MailConfig(**kwargs)
        config.save_entry()
        return f"Email configuration '{config.name}' added successfully."
    except Exception as e:
        logger.error(f"Failed to add email configuration: {str(e)}")
        return f"Can't add email configuration."

def handleUpdateConfig(name: str, **kwargs):
    try:
        config = MailConfig.load_entry(name)
        config.update(**kwargs)
        return f"Email configuration '{name}' updated successfully."
    except Exception as e:
        logger.error(f"Failed to update email configuration: {str(e)}")
        return f"Can't update email '{name}' configuration."

def handleDeleteConfig(name: str):
    try:
        MailConfig.delete_entry(name)
        return f"Email configuration '{name}' deleted successfully."
    except Exception as e:
        logger.error(f"Failed to delete email configuration: {str(e)}")
        return f"Email configuration '{name}' not found."

def handleListConfigs():
    try:
        configs = MailConfig.load_all()
        return [config.name for config in configs]
    except Exception as e:
        logger.error(f"Failed to list email configurations: {str(e)}")
        return []

def handleSendEmail(name: str, subject: str, body: str, to: str):
    config = MailConfig.load_entry(name)
    if not config:
        return f"Email configuration '{name}' not found."
    try:
        if config.outbound_ssl == "SSL/TLS":
            server = smtplib.SMTP_SSL(config.outbound_host, config.outbound_port)
        else:
            server = smtplib.SMTP(config.outbound_host, config.outbound_port)
        if config.outbound_ssl == "STARTTLS":
            server.starttls()
        server.login(config.outbound_user, config.outbound_password)
        message = f"Subject: {subject}\n\n{body}"
        server.sendmail(config.outbound_user, to, message)
        server.quit()
        return f"Email sent successfully."
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return f"Failed to send email: {str(e)}"

def handleLoadFiveLatestEmails(name: str):
    config = MailConfig.load_entry(name)
    if not config:
        return f"Email configuration '{name}' not found."
    try:
        logger.info(f"Loading emails from {config.inbound_host}")
        imap_client = IMAPClient(config.inbound_host, ssl=config.inbound_ssl)
        imap_client.login(config.inbound_user, config.inbound_password)
        imap_client.select_folder('INBOX')
        latest_ids = imap_client.search('ALL')[-5:]
        emails = []
        for uid, message_data in imap_client.fetch(latest_ids, "RFC822").items():
            email_message = email.message_from_bytes(message_data[b"RFC822"])
            logger.info(uid, email_message.get("From"), email_message.get("Subject"))
            emails.append({
                "uid": uid,
                "from": email_message.get("From"),
                "subject": email_message.get("Subject"),
                "body": email_message.get_payload()
                })
        imap_client.logout()
        return emails
    except Exception as e:
        logger.error(f"Failed to load emails: {str(e)}")
        return f"Failed to load emails: {str(e)}"

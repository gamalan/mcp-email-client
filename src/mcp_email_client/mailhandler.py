from .config import MailConfig
import smtplib, imaplib
import logging

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
        if config.inbound_ssl == True:
            mail = imaplib.IMAP4_SSL(config.inbound_host)
        else:
            mail = imaplib.IMAP4(config.inbound_host)
        mail.login(config.inbound_user, config.inbound_password)
        mail.select('inbox')
        _, data = mail.search(None, 'ALL')
        latest_ids = data[0].split()[-5:]
        emails = []
        for email_id in latest_ids:
            _, msg_data = mail.fetch(email_id, '(RFC822)')
            emails.append(msg_data[0][1].decode('utf-8'))
        mail.logout()
        return emails
    except Exception as e:
        logger.error(f"Failed to load emails: {str(e)}")
        return f"Failed to load emails: {str(e)}"

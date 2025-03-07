from .config import MailConfig
import smtplib, imaplib

def handleAddConfig(name: str, **kwargs):
    config = MailConfig(name, **kwargs)
    # Implementation of adding email configuration using the provided name and inbound host
    return f"Email configuration '{config.name}' added successfully."

def handleUpdateConfig(name: str, **kwargs):
    config = MailConfig.load_entry(name)
    config.update(**kwargs)
    return f"Email configuration '{name}' updated successfully."

def handleDeleteConfig(name: str):
    MailConfig.delete_entry(name)
    return f"Email configuration '{name}' deleted successfully."

def handleListConfigs():
    configs = MailConfig.load_all()
    return [config.name for config in configs]

def handleSendEmail(config_name: str, subject: str, body: str, to: str):
    config = MailConfig.load_entry(config_name)
    if not config:
        return f"Email configuration '{config_name}' not found."
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
        return f"Failed to send email: {str(e)}"

def handleLoadFiveLatestEmails(config_name: str):
    config = MailConfig.load_entry(config_name)
    if not config:
        return f"Email configuration '{config_name}' not found."

    try:
        if config.inbound_ssl == "SSL/TLS":
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
        return f"Failed to load emails: {str(e)}"

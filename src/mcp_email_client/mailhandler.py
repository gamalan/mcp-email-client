from mcp_email_client.config import MailConfig
import smtplib, imaplib
import datetime
from email import message_from_bytes
from mcp_email_client.db import (
    insert_email, 
    get_emails, 
    search_emails_by_content, 
    get_emails_by_date_range,
    get_all_emails,
    get_email_count
)
from mcp_email_client.semantic import (
    generate_embedding,
    update_email_with_embedding,
    semantic_search,
    generate_embeddings_for_all
)

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
    result = {}
    for config in configs:
        try:
            with open(config.config_file, 'r') as f:
                file_content = f.read()
                result[config.name] = file_content
        except Exception as e:
            result[config.name] = f"Error reading file: {str(e)}"
    return result

def handleSendEmail(config_name: str, subject: str, body: str, to: str, cc: str = None, bcc: str = None):
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
        
        # Store the sent email in the database
        email_id = insert_email(
            config_name=config_name,
            subject=subject,
            body=body,
            sender=config.outbound_user,
            recipients=to,
            cc=cc,
            bcc=bcc,
            raw_content=message
        )
        
        # Generate and store embedding for the email
        if email_id and subject and body:
            combined_text = f"{subject} {body}"
            update_email_with_embedding(email_id, combined_text)
        
        return f"Email sent successfully."
    except Exception as e:
        return f"Failed to send email: {str(e)}"

def handleLoadHundredLatestEmails(config_name: str):
    config = MailConfig.load_entry(config_name)
    if not config:
        return f"Email configuration '{config_name}' not found."

    try:
        # More comprehensive SSL handling logic
        ssl_value = config.inbound_ssl.lower() if config.inbound_ssl else ""
        
        # Check for any variation of SSL or TLS
        if "ssl" in ssl_value or "tls" in ssl_value:
            # Don't use STARTTLS mode for direct SSL/TLS connection
            if "starttls" not in ssl_value:
                mail = imaplib.IMAP4_SSL(config.inbound_host, config.inbound_port)
            else:
                # Use STARTTLS
                mail = imaplib.IMAP4(config.inbound_host, config.inbound_port)
                mail.starttls()
        else:
            # Plain, unencrypted connection
            mail = imaplib.IMAP4(config.inbound_host, config.inbound_port)
            
        mail.login(config.inbound_user, config.inbound_password)
        mail.select('inbox')
        _, data = mail.search(None, 'ALL')
        
        # Check if we got any email IDs
        if not data or not data[0]:
            return "No emails found in the inbox."
            
        latest_ids = data[0].split()[-100:]  # Get only the 5 latest emails
        emails = []
        
        for email_id in latest_ids:
            _, msg_data = mail.fetch(email_id, '(RFC822)')
            if not msg_data or not msg_data[0]:
                continue
                
            raw_email = msg_data[0][1]
            emails.append(raw_email.decode('utf-8'))
            
            # Parse the email message
            msg = message_from_bytes(raw_email)
            
            # Extract email components
            subject = msg.get('Subject', '')
            from_addr = msg.get('From', '')
            to_addrs = msg.get('To', '')
            cc_addrs = msg.get('Cc', '')
            
            # Get the email body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        try:
                            body = part.get_payload(decode=True).decode()
                            break
                        except:
                            body = "Unable to decode email body"
            else:
                try:
                    body = msg.get_payload(decode=True).decode()
                except:
                    body = "Unable to decode email body"
            
            # Skip database operations for now since they're causing errors
            # Instead, return the parsed email information directly
            emails[-1] = {
                'subject': subject,
                'sender': from_addr,
                'recipients': to_addrs,
                'cc': cc_addrs,
                'body': body[:500] + ('...' if len(body) > 500 else '')  # Truncate long bodies
            }
            email_id = insert_email(
                config_name=config_name,
                subject=subject,
                body=body,
                sender=from_addr,
                recipients=to_addrs,
                cc=cc_addrs,
                bcc=None,  # BCC is not available in received emails
                date=datetime.datetime.now(),
                raw_content=raw_email.decode('utf-8')
            )
            # Generate and store embedding for the email
            if email_id and subject and body:
                combined_text = f"{subject} {body}"
                update_email_with_embedding(email_id, combined_text)
            
        mail.logout()
        
        if not emails:
            return "No emails found in the inbox."
            
        return emails
    except Exception as e:
        return f"Failed to load emails: {str(e)}"

def handleLoadEmailsByDateRange(
    config_name: str, 
    start_date: str, 
    end_date: str = None, 
    limit: int = 100
):
    """Load emails within a specific date range."""
    try:
        # Parse date strings to datetime objects
        start_dt = datetime.datetime.fromisoformat(start_date)
        end_dt = datetime.datetime.fromisoformat(end_date) if end_date else datetime.datetime.now()
        
        # Get emails from the database for the specified date range
        emails = get_emails_by_date_range(
            start_date=start_dt,
            end_date=end_dt,
            config_name=config_name,
            limit=limit
        )
        
        return emails
    except Exception as e:
        return f"Failed to load emails by date range: {str(e)}"

def handleLoadAllEmails(config_name: str = None, limit: int = 1000):
    """Load all emails from the database with optional filtering by config name.
    If there are no emails in the database, load emails from the server."""
    try:
        # Check if there are any emails in the database
        count = get_email_count(config_name=config_name)
        
        # If there are emails, get them from the database as before
        if count > 0:
            emails = get_all_emails(config_name=config_name, limit=limit)
            return emails
        
        # If no emails in database and no config specified, can't load from server
        if not config_name:
            return "No emails in database and no config name specified to load from server."
            
        # Load from server if no emails in database
        config = MailConfig.load_entry(config_name)
        if not config:
            return f"Email configuration '{config_name}' not found."

        try:
            # SSL handling logic from handleLoadHundredLatestEmails
            ssl_value = config.inbound_ssl.lower() if config.inbound_ssl else ""
            
            if "ssl" in ssl_value or "tls" in ssl_value:
                if "starttls" not in ssl_value:
                    mail = imaplib.IMAP4_SSL(config.inbound_host, config.inbound_port)
                else:
                    mail = imaplib.IMAP4(config.inbound_host, config.inbound_port)
                    mail.starttls()
            else:
                mail = imaplib.IMAP4(config.inbound_host, config.inbound_port)
                
            mail.login(config.inbound_user, config.inbound_password)
            mail.select('inbox')
            _, data = mail.search(None, 'ALL')
            
            if not data or not data[0]:
                return "No emails found in the inbox."
                
            latest_ids = data[0].split()
            if len(latest_ids) > limit:
                latest_ids = latest_ids[-limit:]  # Get only the latest 'limit' emails
                
            emails = []
            
            for email_id in latest_ids:
                _, msg_data = mail.fetch(email_id, '(RFC822)')
                if not msg_data or not msg_data[0]:
                    continue
                    
                raw_email = msg_data[0][1]
                
                # Parse the email message
                msg = message_from_bytes(raw_email)
                
                # Extract email components
                subject = msg.get('Subject', '')
                from_addr = msg.get('From', '')
                to_addrs = msg.get('To', '')
                cc_addrs = msg.get('Cc', '')
                
                # Get the email body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            try:
                                body = part.get_payload(decode=True).decode()
                                break
                            except:
                                body = "Unable to decode email body"
                else:
                    try:
                        body = msg.get_payload(decode=True).decode()
                    except:
                        body = "Unable to decode email body"
                
                # Store the email in the database
                email_id = insert_email(
                    config_name=config_name,
                    subject=subject,
                    body=body,
                    sender=from_addr,
                    recipients=to_addrs,
                    cc=cc_addrs,
                    bcc=None,  # BCC is not available in received emails
                    date=datetime.datetime.now(),
                    raw_content=raw_email.decode('utf-8', errors='replace')
                )
                
                # Add parsed email to result list
                emails.append({
                    'id': email_id,
                    'subject': subject,
                    'sender': from_addr,
                    'recipients': to_addrs,
                    'cc': cc_addrs,
                    'body': body[:500] + ('...' if len(body) > 500 else '')  # Truncate long bodies
                })
                
            mail.logout()
            
            if not emails:
                return "No emails found in the inbox."
                
            return emails
            
        except Exception as e:
            return f"Failed to load emails from server: {str(e)}"
            
    except Exception as e:
        return f"Failed to load all emails: {str(e)}"

def handleGetEmailCount(config_name: str = None):
    """Get the total count of emails in the database."""
    try:
        count = get_email_count(config_name=config_name)
        return {"email_count": count}
    except Exception as e:
        return f"Failed to get email count: {str(e)}"

def handleSearchEmails(config_name: str = None, query: str = None, limit: int = 10):
    """Search emails using text search on subject and body"""
    try:
        results = search_emails_by_content(query, config_name, limit)
        return results
    except Exception as e:
        return f"Failed to search emails: {str(e)}"

def handleSemanticSearchEmails(
    query: str, 
    config_name: str = None, 
    similarity_threshold: float = 0.6, 
    limit: int = 10
):
    """Search emails using semantic similarity"""
    try:
        results = semantic_search(
            query=query,
            config_name=config_name,
            similarity_threshold=similarity_threshold,
            limit=limit
        )
        return results
    except Exception as e:
        return f"Failed to perform semantic search: {str(e)}"

def handleGenerateEmbeddings(batch_size: int = 100):
    """Generate embeddings for all emails that don't have them yet"""
    try:
        stats = generate_embeddings_for_all(batch_size=batch_size)
        return stats
    except Exception as e:
        return f"Failed to generate embeddings: {str(e)}"

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.ionos.es")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "aibot@dazzcreative.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "aibot@dazzcreative.com")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "Dazz Creative - Sistema Gastos")
EMAIL_TO = os.getenv("EMAIL_TO", "miguel@dazzle-agency.com")

def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    cc_emails: Optional[List[str]] = None,
    attachments: Optional[List[tuple]] = None
) -> bool:
    """
    Send email via SMTP
    
    Args:
        to_email: Recipient email
        subject: Email subject
        html_body: HTML body content
        cc_emails: List of CC emails (optional)
        attachments: List of tuples (filename, filepath) (optional)
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{EMAIL_FROM_NAME} <{EMAIL_FROM}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add CC
        if cc_emails:
            msg['Cc'] = ', '.join(cc_emails)
        
        # Attach HTML body
        html_part = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Attach files if any
        if attachments:
            for filename, filepath in attachments:
                with open(filepath, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename={filename}')
                    msg.attach(part)
        
        # Connect to SMTP server
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()  # Secure connection
            server.login(SMTP_USER, SMTP_PASSWORD)
            
            # Send email
            recipients = [to_email]
            if cc_emails:
                recipients.extend(cc_emails)
            
            server.send_message(msg, from_addr=EMAIL_FROM, to_addrs=recipients)
        
        return True
    
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def send_project_closed_email(
    project_name: str,
    project_code: str,
    responsible_name: str,
    responsible_email: str,
    tickets_count: int,
    total_amount: float,
    excel_filename: str,
    excel_path: str
) -> bool:
    """Send email when project is closed with Excel attachment"""
    
    subject = f"[Producción Cerrada] {project_name}"
    
    html_body = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;line-height:1.6;color:#333;max-width:600px;margin:0 auto;padding:20px}}.header{{background:linear-gradient(135deg,#f59e0b 0%,#d97706 100%);color:white;padding:30px;border-radius:8px;margin-bottom:30px;text-align:center}}.header h1{{margin:0;font-size:24px;font-weight:bold}}.content{{background:#f9fafb;padding:25px;border-radius:8px;border:1px solid #e5e7eb}}.info-row{{display:flex;justify-content:space-between;padding:12px 0;border-bottom:1px solid #e5e7eb}}.info-row:last-child{{border-bottom:none}}.label{{font-weight:600;color:#6b7280}}.value{{color:#111827}}.total{{font-size:20px;font-weight:bold;color:#f59e0b}}.footer{{margin-top:30px;padding-top:20px;border-top:1px solid #e5e7eb;color:#6b7280;font-size:14px;text-align:center}}.files{{background:white;padding:15px;border-radius:6px;margin-top:20px;border:1px solid #e5e7eb}}.file-item{{padding:10px;display:flex;align-items:center;gap:10px}}</style></head><body><div class="header"><h1>✓ Producción Cerrada</h1></div><div class="content"><p>Hola Miguel,</p><p><strong>{responsible_name}</strong> ha cerrado la siguiente producción:</p><div class="info-row"><span class="label">Proyecto:</span><span class="value">{project_name}</span></div><div class="info-row"><span class="label">Código OC:</span><span class="value">{project_code}</span></div><div class="info-row"><span class="label">Responsable:</span><span class="value">{responsible_name}</span></div><div class="info-row"><span class="label">Total tickets:</span><span class="value">{tickets_count}</span></div><div class="info-row"><span class="label">Importe total:</span><span class="value total">{total_amount:,.2f}€</span></div><div class="files"><strong>📎 Archivo adjunto:</strong><div class="file-item">📊 {excel_filename}</div></div></div><div class="footer"><p>Este email fue enviado automáticamente por el Sistema de Gestión de Gastos de Dazz Creative</p><p>No respondas a este email - aibot@dazzcreative.com</p></div></body></html>"""
    
    attachments = [(excel_filename, excel_path)]
    
    return send_email(
        to_email=EMAIL_TO,
        subject=subject,
        html_body=html_body,
        cc_emails=[responsible_email] if responsible_email else None,
        attachments=attachments
    )

def send_user_created_email(user_name: str, user_email: str, temporary_password: str) -> bool:
    """Send email when new user is created"""
    subject = "Tu cuenta en Dazz Creative - Sistema Gastos"
    html_body = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;line-height:1.6;color:#333;max-width:600px;margin:0 auto;padding:20px}}.header{{background:linear-gradient(135deg,#f59e0b 0%,#d97706 100%);color:white;padding:30px;border-radius:8px;margin-bottom:30px;text-align:center}}.content{{background:#f9fafb;padding:25px;border-radius:8px;border:1px solid #e5e7eb}}.credentials{{background:white;padding:20px;border-radius:6px;border:2px solid #f59e0b;margin:20px 0}}.credential-item{{padding:10px 0;border-bottom:1px solid #e5e7eb}}.credential-item:last-child{{border-bottom:none}}.label{{font-weight:600;color:#6b7280;font-size:12px;text-transform:uppercase}}.value{{font-size:16px;color:#111827;font-family:monospace;background:#fef3c7;padding:5px 10px;border-radius:4px;display:inline-block;margin-top:5px}}.warning{{background:#fef3c7;border-left:4px solid #f59e0b;padding:15px;margin:20px 0;border-radius:4px}}.button{{display:inline-block;background:#f59e0b;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;font-weight:600;margin-top:20px}}.footer{{margin-top:30px;padding-top:20px;border-top:1px solid #e5e7eb;color:#6b7280;font-size:14px;text-align:center}}</style></head><body><div class="header"><h1>👋 Bienvenido/a a Dazz Creative</h1></div><div class="content"><p>Hola <strong>{user_name}</strong>,</p><p>Se ha creado tu cuenta en el Sistema de Gestión de Gastos de Dazz Creative.</p><div class="credentials"><div class="credential-item"><div class="label">Email de acceso:</div><div class="value">{user_email}</div></div><div class="credential-item"><div class="label">Contraseña temporal:</div><div class="value">{temporary_password}</div></div></div><div class="warning"><strong>⚠️ Importante:</strong> Por seguridad, cambia tu contraseña en tu primer inicio de sesión.</div><a href="https://producciones.dazzcreative.com" class="button">Iniciar Sesión</a><p style="margin-top:30px;">Si tienes alguna duda, contacta con tu administrador.</p></div><div class="footer"><p>Sistema de Gestión de Gastos - Dazz Creative</p><p>aibot@dazzcreative.com</p></div></body></html>"""
    return send_email(to_email=user_email, subject=subject, html_body=html_body)

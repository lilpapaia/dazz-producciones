import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.application import MIMEApplication
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


def get_styled_email_template(project_name, project_code, responsible_name, tickets_count, total_amount, excel_filename):
    """Template de email CORREGIDO - Logo grande, full width, sin botón"""
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; background-color: #18181b; color: #f4f4f5;}}
        .container {{max-width: 600px; margin: 0 auto; background-color: #18181b;}}
        .header {{background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 50px 30px; text-align: center;}}
        .logo-container {{display: flex; align-items: center; justify-content: center; gap: 15px; margin-bottom: 20px;}}
        .logo-text {{color: white; font-size: 36px; font-weight: 900; letter-spacing: 0.1em; text-transform: uppercase;}}
        .header h1 {{margin: 15px 0 0 0; font-size: 32px; font-weight: 900; letter-spacing: 0.1em; color: #18181b; text-transform: uppercase;}}
        .content {{background-color: #27272a; margin: 0; padding: 40px 0; border-radius: 0;}}
        .intro {{color: #a1a1aa; font-size: 15px; line-height: 1.6; margin: 0 30px 30px 30px; text-align: center;}}
        .info-grid {{background-color: #18181b; border: none; border-radius: 0; padding: 30px 40px; margin: 0;}}
        .info-row {{display: flex; justify-content: space-between; padding: 16px 0; border-bottom: 1px solid #3f3f46;}}
        .info-row:last-child {{border-bottom: none; padding-bottom: 0;}}
        .info-label {{color: #71717a; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em;}}
        .info-value {{color: #f4f4f5; font-size: 16px; font-weight: 600; text-align: right; letter-spacing: 0.02em;}}
        .total-amount {{font-size: 32px; font-weight: 900; color: #f59e0b;}}
        .attachment-box {{background: linear-gradient(135deg, #f59e0b20 0%, #d9770620 100%); border: 2px solid #f59e0b40; border-radius: 8px; padding: 30px; margin: 30px 30px; text-align: center;}}
        .attachment-icon {{font-size: 48px; margin-bottom: 15px;}}
        .attachment-title {{color: #f59e0b; font-size: 18px; font-weight: 700; margin-bottom: 10px; letter-spacing: 0.05em;}}
        .attachment-filename {{color: #a1a1aa; font-size: 15px; font-family: 'Courier New', monospace; word-break: break-all;}}
        .footer {{text-align: center; padding: 40px 30px; color: #71717a; font-size: 13px; line-height: 1.8;}}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo-container">
                <svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" viewBox="0 0 66 69" fill="none">
                    <path d="M58.7442 59.5633L46.4651 68.332L32.7907 50.377L19.5349 68.332L6.97674 59.5633L20.3721 40.634L0 34.2314L4.60465 20.1736L24.5581 26.5761V3.33203H41.0233V26.5761L60.9767 20.1736L66 34.2314L45.3488 40.634L58.7442 59.5633Z" fill="white"/>
                </svg>
                <span class="logo-text">DAZZ CREATIVE</span>
            </div>
            <h1>✓ PRODUCCIÓN CERRADA</h1>
        </div>
        <div class="content">
            <p class="intro">Se ha cerrado la siguiente producción:</p>
            <div class="info-grid">
                <div class="info-row"><span class="info-label">Proyecto</span><span class="info-value">{project_name}</span></div>
                <div class="info-row"><span class="info-label">Código OC</span><span class="info-value">{project_code}</span></div>
                <div class="info-row"><span class="info-label">Responsable</span><span class="info-value">{responsible_name}</span></div>
                <div class="info-row"><span class="info-label">Total Tickets</span><span class="info-value">{tickets_count}</span></div>
                <div class="info-row"><span class="info-label">Importe Total</span><span class="info-value total-amount">{total_amount:,.2f}€</span></div>
            </div>
            <div class="attachment-box">
                <div class="attachment-icon">📊</div>
                <div class="attachment-title">ARCHIVO ADJUNTO</div>
                <div class="attachment-filename">{excel_filename}</div>
            </div>
        </div>
        <div class="footer">
            <svg xmlns="http://www.w3.org/2000/svg" width="120" height="12" viewBox="0 0 708 69" fill="none" style="margin-bottom: 20px;">
                <path d="M58.7442 59.5633L46.4651 68.332L32.7907 50.377L19.5349 68.332L6.97674 59.5633L20.3721 40.634L0 34.2314L4.60465 20.1736L24.5581 26.5761V3.33203H41.0233V26.5761L60.9767 20.1736L66 34.2314L45.3488 40.634L58.7442 59.5633Z" fill="#71717a"/>
                <path d="M117.987 55.1217H129.049C140.689 55.1217 145.691 47.8108 145.691 33.3812C145.691 18.9517 140.689 13.1798 127.895 13.1798H117.987V55.1217ZM131.743 65.992H105V2.11719H129.723C147.038 2.11719 159.351 13.9494 159.351 33.3812C159.351 52.813 148.289 65.992 131.743 65.992Z" fill="#71717a"/>
                <path d="M192.939 41.8466L184.955 16.4505H184.859L176.682 41.8466H192.939ZM215.353 65.992H200.827L196.787 52.813H173.219L168.698 65.992H154.557L177.355 2.11719H192.843L215.353 65.992Z" fill="#71717a"/>
                <path d="M266.393 65.992H216.467V54.6408L249.655 13.276H217.429V2.11719H266.393V12.6027L233.013 54.6408H266.393V65.992Z" fill="#71717a"/>
                <path d="M319.283 65.992H269.356V54.6408L302.544 13.276H270.318V2.11719H319.283V12.6027L285.902 54.6408H319.283V65.992Z" fill="#71717a"/>
            </svg>
            <p>Este email fue enviado automáticamente por el<br><strong>Sistema de Gestión de Gastos de Dazz Creative</strong></p>
            <p style="color: #52525b; margin-top: 15px;">No respondas a este email</p>
        </div>
    </div>
</body>
</html>"""
    
    return html


def send_email(to_email: str, subject: str, html_body: str, cc_emails: Optional[List[str]] = None, attachments: Optional[List[tuple]] = None) -> bool:
    """Send email via SMTP"""
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{EMAIL_FROM_NAME} <{EMAIL_FROM}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        
        if cc_emails:
            msg['Cc'] = ', '.join(cc_emails)
        
        html_part = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(html_part)
        
        if attachments:
            for filename, filepath in attachments:
                with open(filepath, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename={filename}')
                    msg.attach(part)
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            recipients = [to_email]
            if cc_emails:
                recipients.extend(cc_emails)
            server.send_message(msg, from_addr=EMAIL_FROM, to_addrs=recipients)
        
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False


def send_project_closed_email_multi(recipients: List[str], project_name: str, project_code: str, responsible_name: str, tickets_count: int, total_amount: float, excel_bytes: bytes, excel_filename: str) -> bool:
    """Envía email con Excel adjunto a múltiples destinatarios - VERSIÓN CORREGIDA"""
    try:
        if not SMTP_USER or not SMTP_PASSWORD:
            print("⚠️ SMTP_USER o SMTP_PASSWORD no configurados")
            return False
        
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{EMAIL_FROM_NAME} <{EMAIL_FROM}>"
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = f"[Producción Cerrada] {project_code} - {project_name}"
        
        # Usar template CORREGIDO
        html_body = get_styled_email_template(
            project_name, 
            project_code, 
            responsible_name, 
            tickets_count, 
            total_amount, 
            excel_filename
        )
        
        html_part = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Adjuntar Excel desde bytes
        part = MIMEApplication(excel_bytes, Name=excel_filename)
        part['Content-Disposition'] = f'attachment; filename="{excel_filename}"'
        msg.attach(part)
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg, from_addr=EMAIL_FROM, to_addrs=recipients)
        
        print(f"✅ Email enviado correctamente a: {', '.join(recipients)}")
        return True
        
    except Exception as e:
        print(f"❌ Error enviando email: {str(e)}")
        return False


def send_user_created_email(user_name: str, user_email: str, temporary_password: str) -> bool:
    """Send email when new user is created"""
    subject = "Tu cuenta en Dazz Creative - Sistema Gastos"
    html_body = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;line-height:1.6;color:#333;max-width:600px;margin:0 auto;padding:20px}}.header{{background:linear-gradient(135deg,#f59e0b 0%,#d97706 100%);color:white;padding:30px;border-radius:8px;margin-bottom:30px;text-align:center}}.content{{background:#f9fafb;padding:25px;border-radius:8px;border:1px solid #e5e7eb}}.credentials{{background:white;padding:20px;border-radius:6px;border:2px solid #f59e0b;margin:20px 0}}.credential-item{{padding:10px 0;border-bottom:1px solid #e5e7eb}}.credential-item:last-child{{border-bottom:none}}.label{{font-weight:600;color:#6b7280;font-size:12px;text-transform:uppercase}}.value{{font-size:16px;color:#111827;font-family:monospace;background:#fef3c7;padding:5px 10px;border-radius:4px;display:inline-block;margin-top:5px}}.warning{{background:#fef3c7;border-left:4px solid #f59e0b;padding:15px;margin:20px 0;border-radius:4px}}.button{{display:inline-block;background:#f59e0b;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;font-weight:600;margin-top:20px}}.footer{{margin-top:30px;padding-top:20px;border-top:1px solid #e5e7eb;color:#6b7280;font-size:14px;text-align:center}}</style></head><body><div class="header"><h1>👋 Bienvenido/a a Dazz Creative</h1></div><div class="content"><p>Hola <strong>{user_name}</strong>,</p><p>Se ha creado tu cuenta en el Sistema de Gestión de Gastos de Dazz Creative.</p><div class="credentials"><div class="credential-item"><div class="label">Email de acceso:</div><div class="value">{user_email}</div></div><div class="credential-item"><div class="label">Contraseña temporal:</div><div class="value">{temporary_password}</div></div></div><div class="warning"><strong>⚠️ Importante:</strong> Por seguridad, cambia tu contraseña en tu primer inicio de sesión.</div><a href="https://producciones.dazzcreative.com" class="button">Iniciar Sesión</a><p style="margin-top:30px;">Si tienes alguna duda, contacta con tu administrador.</p></div><div class="footer"><p>Sistema de Gestión de Gastos - Dazz Creative</p><p>aibot@dazzcreative.com</p></div></body></html>"""
    return send_email(to_email=user_email, subject=subject, html_body=html_body)

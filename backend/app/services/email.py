"""
EMAIL SERVICE - BREVO API
==========================
Usa API REST (HTTPS) en lugar de SMTP.
Railway bloquea SMTP, pero API funciona.
"""

import httpx
import os
from dotenv import load_dotenv

load_dotenv()

# Brevo API
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"

# Configuración remitente
FROM_EMAIL = os.getenv("FROM_EMAIL", "aibot2@dazzcreative.com")
FROM_NAME = os.getenv("FROM_NAME", "DAZZ Creative")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://producciones.dazzcreative.com")


def send_email(to_email: str, subject: str, html_content: str):
    """Función base para enviar emails HTML via Brevo API"""
    
    if not BREVO_API_KEY:
        raise Exception("BREVO_API_KEY no configurada")
    
    payload = {
        "sender": {
            "name": FROM_NAME,
            "email": FROM_EMAIL
        },
        "to": [
            {"email": to_email}
        ],
        "subject": subject,
        "htmlContent": html_content
    }
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(BREVO_API_URL, json=payload, headers=headers)
            
            if response.status_code in [200, 201]:
                print(f"✅ Email enviado a {to_email}")
                return True
            else:
                error_data = response.json()
                error_msg = error_data.get("message", response.text)
                print(f"❌ Error Brevo ({response.status_code}): {error_msg}")
                raise Exception(f"Error Brevo: {error_msg}")
                
    except httpx.TimeoutException:
        print(f"❌ Timeout enviando email a {to_email}")
        raise Exception("Timeout conectando con Brevo API")
    except Exception as e:
        print(f"❌ Error enviando email: {str(e)}")
        raise e


def send_set_password_email(user_name: str, user_email: str, token: str):
    """
    Enviar email con link para que el usuario elija su contraseña
    
    Args:
        user_name: Nombre del usuario
        user_email: Email del usuario
        token: Token único para set password
    """
    set_password_url = f"{FRONTEND_URL}/set-password?token={token}"
    
    subject = "¡Bienvenido a DAZZ Creative! - Configura tu contraseña"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #18181b;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #18181b; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #27272a; border-radius: 8px; overflow: hidden;">
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 40px; text-align: center;">
                                <div style="display: inline-block; width: 60px; height: 60px; background-color: rgba(255,255,255,0.2); border-radius: 50%; padding: 15px; margin-bottom: 15px;">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" style="width: 100%; height: 100%;" stroke-width="2.5" stroke-linecap="round">
                                        <line x1="12" y1="3" x2="12" y2="21" />
                                        <line x1="3" y1="12" x2="21" y2="12" />
                                        <line x1="5.5" y1="5.5" x2="18.5" y2="18.5" />
                                        <line x1="18.5" y1="5.5" x2="5.5" y2="18.5" />
                                    </svg>
                                </div>
                                <h1 style="margin: 0; color: #ffffff; font-size: 32px; font-weight: bold; letter-spacing: 2px;">
                                    DAZZ CREATIVE
                                </h1>
                                <p style="margin: 10px 0 0 0; color: rgba(255,255,255,0.8); font-size: 12px; letter-spacing: 3px;">
                                    SISTEMA GESTIÓN GASTOS
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="margin: 0 0 20px 0; color: #f59e0b; font-size: 24px;">
                                    ¡Bienvenido, {user_name}!
                                </h2>
                                
                                <p style="margin: 0 0 20px 0; color: #d4d4d8; font-size: 16px; line-height: 1.6;">
                                    Tu cuenta ha sido creada en el sistema de gestión de producciones de DAZZ Creative.
                                </p>
                                
                                <p style="margin: 0 0 30px 0; color: #d4d4d8; font-size: 16px; line-height: 1.6;">
                                    Para comenzar, necesitas <strong style="color: #f59e0b;">configurar tu contraseña</strong>. 
                                    Haz clic en el botón de abajo para elegir una contraseña segura:
                                </p>
                                
                                <!-- Button -->
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td align="center" style="padding: 20px 0;">
                                            <a href="{set_password_url}" 
                                               style="display: inline-block; padding: 16px 40px; background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: #000000; text-decoration: none; font-weight: bold; font-size: 16px; border-radius: 4px; letter-spacing: 1px; box-shadow: 0 4px 6px rgba(245, 158, 11, 0.3);">
                                                CONFIGURAR CONTRASEÑA
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                                
                                <p style="margin: 30px 0 10px 0; color: #a1a1aa; font-size: 14px; line-height: 1.6;">
                                    O copia y pega este enlace en tu navegador:
                                </p>
                                <p style="margin: 0; padding: 12px; background-color: #18181b; border-radius: 4px; word-break: break-all;">
                                    <a href="{set_password_url}" style="color: #f59e0b; text-decoration: none; font-size: 13px;">
                                        {set_password_url}
                                    </a>
                                </p>
                                
                                <div style="margin-top: 30px; padding: 20px; background-color: #3f3f46; border-left: 4px solid #f59e0b; border-radius: 4px;">
                                    <p style="margin: 0; color: #e4e4e7; font-size: 14px; line-height: 1.6;">
                                        <strong style="color: #f59e0b;">⚠️ Importante:</strong> Este enlace expirará en <strong>24 horas</strong>. 
                                        Si no configuras tu contraseña a tiempo, contacta con tu administrador.
                                    </p>
                                </div>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #18181b; padding: 30px; text-align: center; border-top: 1px solid #3f3f46;">
                                <p style="margin: 0 0 10px 0; color: #71717a; font-size: 13px;">
                                    Este email fue enviado desde el Sistema de Gestión de Producciones
                                </p>
                                <p style="margin: 0; color: #52525b; font-size: 12px;">
                                    © 2026 DAZZ Creative. Todos los derechos reservados.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    return send_email(user_email, subject, html_content)


def send_user_created_email(user_name: str, user_email: str, temporary_password: str):
    """
    Email antiguo - Ahora solo se usa si NO se genera token
    Mantenerlo por compatibilidad
    """
    subject = "Bienvenido a DAZZ Creative - Credenciales de acceso"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px;">
            <h2 style="color: #333;">Bienvenido a DAZZ Creative</h2>
            <p>Hola {user_name},</p>
            <p>Tu cuenta ha sido creada en el sistema de gestión de producciones.</p>
            <div style="background-color: #f8f8f8; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 5px 0;"><strong>Email:</strong> {user_email}</p>
                <p style="margin: 5px 0;"><strong>Contraseña temporal:</strong> {temporary_password}</p>
            </div>
            <p>Accede al sistema: <a href="{FRONTEND_URL}/login">https://producciones.dazzcreative.com</a></p>
            <p style="color: #666; font-size: 12px; margin-top: 30px;">Por favor, cambia tu contraseña después de iniciar sesión por primera vez.</p>
        </div>
    </body>
    </html>
    """
    
    return send_email(user_email, subject, html_content)


def send_forgot_password_email(user_name: str, user_email: str, token: str):
    """
    Enviar email para restablecer contraseña olvidada
    """
    reset_url = f"{FRONTEND_URL}/set-password?token={token}"
    
    subject = "DAZZ Creative - Restablecer contraseña"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #18181b;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #18181b; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #27272a; border-radius: 8px; overflow: hidden;">
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 40px; text-align: center;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 32px; font-weight: bold; letter-spacing: 2px;">
                                    DAZZ CREATIVE
                                </h1>
                                <p style="margin: 10px 0 0 0; color: rgba(255,255,255,0.8); font-size: 12px; letter-spacing: 3px;">
                                    RESTABLECER CONTRASEÑA
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="margin: 0 0 20px 0; color: #f59e0b; font-size: 24px;">
                                    Hola, {user_name}
                                </h2>
                                
                                <p style="margin: 0 0 20px 0; color: #d4d4d8; font-size: 16px; line-height: 1.6;">
                                    Hemos recibido una solicitud para restablecer la contraseña de tu cuenta.
                                </p>
                                
                                <p style="margin: 0 0 30px 0; color: #d4d4d8; font-size: 16px; line-height: 1.6;">
                                    Haz clic en el botón de abajo para crear una nueva contraseña:
                                </p>
                                
                                <!-- Button -->
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td align="center" style="padding: 20px 0;">
                                            <a href="{reset_url}" 
                                               style="display: inline-block; padding: 16px 40px; background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: #000000; text-decoration: none; font-weight: bold; font-size: 16px; border-radius: 4px; letter-spacing: 1px;">
                                                RESTABLECER CONTRASEÑA
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                                
                                <p style="margin: 30px 0 10px 0; color: #a1a1aa; font-size: 14px; line-height: 1.6;">
                                    O copia y pega este enlace en tu navegador:
                                </p>
                                <p style="margin: 0; padding: 12px; background-color: #18181b; border-radius: 4px; word-break: break-all;">
                                    <a href="{reset_url}" style="color: #f59e0b; text-decoration: none; font-size: 13px;">
                                        {reset_url}
                                    </a>
                                </p>
                                
                                <div style="margin-top: 30px; padding: 20px; background-color: #3f3f46; border-left: 4px solid #ef4444; border-radius: 4px;">
                                    <p style="margin: 0; color: #e4e4e7; font-size: 14px; line-height: 1.6;">
                                        <strong style="color: #ef4444;">⚠️ Importante:</strong> Este enlace expirará en <strong>1 hora</strong>. 
                                        Si no solicitaste este cambio, ignora este email.
                                    </p>
                                </div>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #18181b; padding: 30px; text-align: center; border-top: 1px solid #3f3f46;">
                                <p style="margin: 0 0 10px 0; color: #71717a; font-size: 13px;">
                                    Este email fue enviado desde el Sistema de Gestión de Producciones
                                </p>
                                <p style="margin: 0; color: #52525b; font-size: 12px;">
                                    © 2026 DAZZ Creative. Todos los derechos reservados.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    return send_email(user_email, subject, html_content)


def send_project_closed_email(recipients: list, project_data: dict):
    """Enviar email cuando se cierra un proyecto"""
    # TODO: Implementar si se necesita
    pass


def send_project_closed_email_multi(
    recipients: list,
    project_name: str,
    project_code: str,
    responsible_name: str,
    tickets_count: int,
    total_amount: float,
    excel_bytes: bytes,
    excel_filename: str
):
    """
    Enviar email de proyecto cerrado con Excel adjunto a múltiples destinatarios.
    Usa Brevo API.
    """
    import base64
    
    if not BREVO_API_KEY:
        raise Exception("BREVO_API_KEY no configurada")
    
    subject = f"📊 Proyecto Cerrado: {project_code}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #18181b;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #18181b; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #27272a; border-radius: 8px; overflow: hidden;">
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%); padding: 40px; text-align: center;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 32px; font-weight: bold; letter-spacing: 2px;">
                                    DAZZ CREATIVE
                                </h1>
                                <p style="margin: 10px 0 0 0; color: rgba(255,255,255,0.9); font-size: 14px; letter-spacing: 3px;">
                                    ✅ PROYECTO CERRADO
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="margin: 0 0 20px 0; color: #22c55e; font-size: 24px;">
                                    {project_code}
                                </h2>
                                
                                <p style="margin: 0 0 20px 0; color: #d4d4d8; font-size: 16px; line-height: 1.6;">
                                    {project_name}
                                </p>
                                
                                <!-- Resumen -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="margin: 20px 0; background-color: #3f3f46; border-radius: 4px;">
                                    <tr>
                                        <td style="padding: 20px;">
                                            <table width="100%" cellpadding="0" cellspacing="0">
                                                <tr>
                                                    <td style="padding: 10px 0; border-bottom: 1px solid #52525b;">
                                                        <span style="color: #a1a1aa; font-size: 12px;">RESPONSABLE</span><br>
                                                        <span style="color: #ffffff; font-size: 16px; font-weight: bold;">{responsible_name}</span>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="padding: 10px 0; border-bottom: 1px solid #52525b;">
                                                        <span style="color: #a1a1aa; font-size: 12px;">TICKETS</span><br>
                                                        <span style="color: #ffffff; font-size: 16px; font-weight: bold;">{tickets_count} tickets</span>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="padding: 10px 0;">
                                                        <span style="color: #a1a1aa; font-size: 12px;">IMPORTE TOTAL</span><br>
                                                        <span style="color: #f59e0b; font-size: 24px; font-weight: bold;">{total_amount:.2f}€</span>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                                
                                <p style="margin: 20px 0; color: #a1a1aa; font-size: 14px;">
                                    📎 Se adjunta el archivo Excel con el desglose completo de gastos.
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #18181b; padding: 30px; text-align: center; border-top: 1px solid #3f3f46;">
                                <p style="margin: 0 0 10px 0; color: #71717a; font-size: 13px;">
                                    Este email fue enviado desde el Sistema de Gestión de Producciones
                                </p>
                                <p style="margin: 0; color: #52525b; font-size: 12px;">
                                    © 2026 DAZZ Creative. Todos los derechos reservados.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    # Convertir Excel a base64 para adjunto
    excel_base64 = base64.b64encode(excel_bytes).decode('utf-8')
    
    # Preparar lista de destinatarios
    to_list = [{"email": email} for email in recipients]
    
    payload = {
        "sender": {
            "name": FROM_NAME,
            "email": FROM_EMAIL
        },
        "to": to_list,
        "subject": subject,
        "htmlContent": html_content,
        "attachment": [
            {
                "content": excel_base64,
                "name": excel_filename
            }
        ]
    }
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY
    }
    
    try:
        with httpx.Client(timeout=60.0) as client:  # Más tiempo para adjuntos
            response = client.post(BREVO_API_URL, json=payload, headers=headers)
            
            if response.status_code in [200, 201]:
                print(f"✅ Email proyecto cerrado enviado a {len(recipients)} destinatarios")
                return True
            else:
                error_data = response.json()
                error_msg = error_data.get("message", response.text)
                print(f"❌ Error Brevo ({response.status_code}): {error_msg}")
                raise Exception(f"Error Brevo: {error_msg}")
                
    except httpx.TimeoutException:
        print(f"❌ Timeout enviando email de proyecto cerrado")
        raise Exception("Timeout conectando con Brevo API")
    except Exception as e:
        print(f"❌ Error enviando email proyecto cerrado: {str(e)}")
        raise e


# ============================================
# TEST - Para verificar que funciona
# ============================================
def test_brevo_connection():
    """Prueba la conexión con Brevo API."""
    
    if not BREVO_API_KEY:
        return {"success": False, "error": "BREVO_API_KEY no configurada"}
    
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY
    }
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get("https://api.brevo.com/v3/account", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "account_email": data.get("email"),
                    "plan": data.get("plan", [{}])[0].get("type", "unknown"),
                    "credits": data.get("plan", [{}])[0].get("credits", "unknown")
                }
            else:
                return {"success": False, "error": f"API error: {response.status_code}"}
                
    except Exception as e:
        return {"success": False, "error": str(e)}

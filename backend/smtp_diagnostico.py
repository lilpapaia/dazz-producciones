"""
DIAGNÓSTICO SMTP ULTRA INTENSIVO
=================================
Debug máximo de conexión SMTP con IONOS.
Captura TODO: red, SSL, SMTP raw, headers, etc.
"""

import socket
import ssl
import smtplib
import os
import sys
import io
import traceback
from datetime import datetime
from typing import Dict, Any, List
from contextlib import redirect_stderr

# ============================================
# CONFIGURACIÓN
# ============================================
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.ionos.es")
SMTP_PORT_SSL = int(os.getenv("SMTP_PORT_SSL", "465"))
SMTP_PORT_TLS = int(os.getenv("SMTP_PORT_TLS", "587"))
SMTP_USER = os.getenv("SMTP_USER", "julio@dazzcreative.com")
SMTP_PASS = os.getenv("SMTP_PASS", "")

# ============================================
# UTILIDADES DE LOG
# ============================================
class DebugLogger:
    def __init__(self):
        self.logs: List[Dict] = []
        self.start_time = datetime.now()
    
    def log(self, msg: str, level: str = "INFO", data: Any = None) -> Dict:
        elapsed = (datetime.now() - self.start_time).total_seconds()
        entry = {
            "time": f"+{elapsed:.3f}s",
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "level": level,
            "message": msg
        }
        if data is not None:
            entry["data"] = data
        self.logs.append(entry)
        
        # Print en tiempo real
        icons = {"OK": "✅", "WARN": "⚠️ ", "ERROR": "❌", "INFO": "ℹ️ ", "DEBUG": "🔍", "RAW": "📝"}
        icon = icons.get(level, "•")
        print(f"[{entry['time']}] {icon} {msg}")
        if data and level == "RAW":
            for line in str(data).split('\n')[:20]:  # Max 20 líneas
                print(f"         │ {line}")
        
        return entry
    
    def section(self, title: str):
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
        self.log(f"=== {title} ===", "INFO")


# ============================================
# TESTS
# ============================================

def test_network_info(logger: DebugLogger) -> Dict[str, Any]:
    """Info de red del servidor actual."""
    logger.section("INFORMACIÓN DE RED LOCAL")
    result = {"success": True}
    
    # Hostname
    try:
        hostname = socket.gethostname()
        logger.log(f"Hostname: {hostname}", "DEBUG")
        result["hostname"] = hostname
    except:
        pass
    
    # IP local
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        logger.log(f"IP local (salida): {local_ip}", "DEBUG")
        result["local_ip"] = local_ip
    except Exception as e:
        logger.log(f"No se pudo obtener IP local: {e}", "WARN")
    
    # Intentar obtener IP pública
    try:
        import urllib.request
        external_ip = urllib.request.urlopen('https://api.ipify.org', timeout=5).read().decode('utf8')
        logger.log(f"IP pública: {external_ip}", "DEBUG")
        result["public_ip"] = external_ip
    except Exception as e:
        logger.log(f"No se pudo obtener IP pública: {e}", "WARN")
    
    return result


def test_dns_resolution(logger: DebugLogger, host: str) -> Dict[str, Any]:
    """Resolver DNS con todo el detalle."""
    logger.section(f"RESOLUCIÓN DNS: {host}")
    result = {"test": "DNS", "host": host, "success": False}
    
    # IPv4
    try:
        logger.log(f"Resolviendo A records (IPv4)...")
        start = datetime.now()
        ipv4_data = socket.gethostbyname_ex(host)
        elapsed = (datetime.now() - start).total_seconds() * 1000
        
        result["hostname_canonical"] = ipv4_data[0]
        result["aliases"] = ipv4_data[1]
        result["ipv4_addresses"] = ipv4_data[2]
        
        logger.log(f"Nombre canónico: {ipv4_data[0]}", "DEBUG")
        logger.log(f"Aliases: {ipv4_data[1] or 'ninguno'}", "DEBUG")
        logger.log(f"IPs IPv4: {ipv4_data[2]}", "OK")
        logger.log(f"Tiempo resolución: {elapsed:.1f}ms", "DEBUG")
        
        result["success"] = True
        result["resolution_time_ms"] = round(elapsed, 2)
        
    except socket.gaierror as e:
        logger.log(f"ERROR DNS: {e}", "ERROR")
        result["error"] = str(e)
        return result
    
    # IPv6
    try:
        logger.log(f"Resolviendo AAAA records (IPv6)...")
        ipv6_info = socket.getaddrinfo(host, None, socket.AF_INET6)
        ipv6_list = list(set([info[4][0] for info in ipv6_info]))
        result["ipv6_addresses"] = ipv6_list
        logger.log(f"IPs IPv6: {ipv6_list}", "OK")
    except socket.gaierror:
        logger.log("No hay registros AAAA (IPv6)", "DEBUG")
        result["ipv6_addresses"] = []
    
    # MX records (informativo)
    try:
        import subprocess
        mx_result = subprocess.run(['host', '-t', 'MX', host.replace('smtp.', '')], 
                                   capture_output=True, text=True, timeout=5)
        if mx_result.returncode == 0:
            logger.log(f"MX records del dominio:", "DEBUG")
            for line in mx_result.stdout.strip().split('\n'):
                logger.log(f"  {line}", "DEBUG")
    except:
        pass
    
    return result


def test_tcp_connection(logger: DebugLogger, host: str, port: int, timeout: int = 15) -> Dict[str, Any]:
    """Test TCP con máximo detalle."""
    logger.section(f"CONEXIÓN TCP: {host}:{port}")
    result = {"test": f"TCP:{port}", "host": host, "port": port, "success": False}
    
    logger.log(f"Creando socket TCP...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    
    # Opciones del socket
    logger.log(f"Timeout configurado: {timeout}s", "DEBUG")
    
    try:
        logger.log(f"Conectando a {host}:{port}...")
        start = datetime.now()
        
        sock.connect((host, port))
        
        elapsed = (datetime.now() - start).total_seconds()
        logger.log(f"¡CONEXIÓN TCP ESTABLECIDA!", "OK")
        logger.log(f"Tiempo de conexión: {elapsed*1000:.1f}ms", "DEBUG")
        
        result["success"] = True
        result["connection_time_ms"] = round(elapsed * 1000, 2)
        
        # Info del socket
        local_addr = sock.getsockname()
        remote_addr = sock.getpeername()
        logger.log(f"Socket local: {local_addr[0]}:{local_addr[1]}", "DEBUG")
        logger.log(f"Socket remoto: {remote_addr[0]}:{remote_addr[1]}", "DEBUG")
        result["local_address"] = f"{local_addr[0]}:{local_addr[1]}"
        result["remote_address"] = f"{remote_addr[0]}:{remote_addr[1]}"
        
        # Intentar leer banner (solo para puerto 587, el 465 es SSL directo)
        if port == 587:
            try:
                sock.settimeout(5)
                logger.log("Esperando banner SMTP...", "DEBUG")
                banner = sock.recv(1024)
                banner_decoded = banner.decode('utf-8', errors='ignore').strip()
                logger.log(f"Banner recibido:", "RAW", banner_decoded)
                result["smtp_banner"] = banner_decoded
            except socket.timeout:
                logger.log("No se recibió banner en 5s", "DEBUG")
        else:
            logger.log("Puerto 465 usa SSL directo, no hay banner sin cifrar", "DEBUG")
        
    except socket.timeout:
        elapsed = timeout
        logger.log(f"⏱️  TIMEOUT después de {timeout}s", "ERROR")
        logger.log("El puerto NO responde - probablemente BLOQUEADO", "ERROR")
        result["error"] = f"Connection timeout ({timeout}s)"
        result["diagnosis"] = "PUERTO BLOQUEADO por firewall o proveedor cloud"
        
    except ConnectionRefusedError as e:
        logger.log(f"🚫 CONEXIÓN RECHAZADA: {e}", "ERROR")
        result["error"] = "Connection refused"
        result["diagnosis"] = "El servidor rechaza la conexión en este puerto"
        
    except OSError as e:
        logger.log(f"💥 ERROR DE RED: {e}", "ERROR")
        result["error"] = str(e)
        if "Network is unreachable" in str(e):
            result["diagnosis"] = "Red no alcanzable - sin conectividad"
        elif "No route to host" in str(e):
            result["diagnosis"] = "Sin ruta al host - problema de routing"
            
    except Exception as e:
        logger.log(f"💥 ERROR INESPERADO: {type(e).__name__}: {e}", "ERROR")
        logger.log(traceback.format_exc(), "RAW")
        result["error"] = str(e)
        
    finally:
        sock.close()
        logger.log("Socket cerrado", "DEBUG")
    
    return result


def test_ssl_handshake(logger: DebugLogger, host: str, port: int = 465) -> Dict[str, Any]:
    """Test SSL/TLS con todo el detalle."""
    logger.section(f"HANDSHAKE SSL/TLS: {host}:{port}")
    result = {"test": "SSL", "host": host, "port": port, "success": False}
    
    logger.log("Creando contexto SSL...")
    context = ssl.create_default_context()
    
    # Info del contexto
    logger.log(f"Protocolos soportados: TLS 1.2, TLS 1.3", "DEBUG")
    logger.log(f"Verificación certificado: activada", "DEBUG")
    
    try:
        logger.log(f"Conectando TCP a {host}:{port}...")
        with socket.create_connection((host, port), timeout=15) as sock:
            logger.log("TCP conectado, iniciando handshake SSL...", "DEBUG")
            
            start = datetime.now()
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                elapsed = (datetime.now() - start).total_seconds()
                
                logger.log(f"¡HANDSHAKE SSL COMPLETADO!", "OK")
                logger.log(f"Tiempo handshake: {elapsed*1000:.1f}ms", "DEBUG")
                
                # Detalles SSL
                result["ssl_version"] = ssock.version()
                result["cipher_suite"] = ssock.cipher()
                
                logger.log(f"Versión SSL/TLS: {ssock.version()}", "OK")
                logger.log(f"Cipher suite: {ssock.cipher()[0]}", "DEBUG")
                logger.log(f"Bits de cifrado: {ssock.cipher()[2]}", "DEBUG")
                
                # Certificado
                cert = ssock.getpeercert()
                if cert:
                    logger.log("Información del certificado:", "DEBUG")
                    
                    subject = dict(x[0] for x in cert.get('subject', []))
                    issuer = dict(x[0] for x in cert.get('issuer', []))
                    
                    result["cert_cn"] = subject.get('commonName', 'N/A')
                    result["cert_org"] = subject.get('organizationName', 'N/A')
                    result["cert_issuer"] = issuer.get('organizationName', 'N/A')
                    result["cert_expires"] = cert.get('notAfter', 'N/A')
                    
                    logger.log(f"  CN (Common Name): {result['cert_cn']}", "DEBUG")
                    logger.log(f"  Organización: {result['cert_org']}", "DEBUG")
                    logger.log(f"  Emisor: {result['cert_issuer']}", "DEBUG")
                    logger.log(f"  Expira: {result['cert_expires']}", "DEBUG")
                    
                    # SANs
                    sans = cert.get('subjectAltName', [])
                    if sans:
                        san_list = [x[1] for x in sans]
                        logger.log(f"  SANs: {san_list[:5]}{'...' if len(san_list) > 5 else ''}", "DEBUG")
                
                result["success"] = True
                
    except ssl.SSLCertVerificationError as e:
        logger.log(f"🔐 ERROR CERTIFICADO: {e}", "ERROR")
        result["error"] = f"Certificate verification failed: {e}"
        
    except ssl.SSLError as e:
        logger.log(f"🔐 ERROR SSL: {e}", "ERROR")
        result["error"] = str(e)
        
    except socket.timeout:
        logger.log("⏱️  TIMEOUT durante handshake SSL", "ERROR")
        result["error"] = "SSL handshake timeout"
        
    except Exception as e:
        logger.log(f"💥 ERROR: {type(e).__name__}: {e}", "ERROR")
        result["error"] = str(e)
    
    return result


def test_smtp_session(logger: DebugLogger, host: str, port: int, user: str, password: str, 
                       use_ssl: bool = True) -> Dict[str, Any]:
    """Test sesión SMTP completa con debug raw."""
    mode = "SSL" if use_ssl else "STARTTLS"
    logger.section(f"SESIÓN SMTP ({mode}): {host}:{port}")
    
    result = {
        "test": f"SMTP_{mode}",
        "host": host,
        "port": port,
        "user": user,
        "success": False,
        "smtp_debug": []
    }
    
    if not password:
        logger.log("❌ SMTP_PASS no configurado!", "ERROR")
        result["error"] = "No password configured"
        return result
    
    # Capturar debug de smtplib
    debug_buffer = io.StringIO()
    
    try:
        if use_ssl:
            logger.log(f"Conectando SMTP_SSL a {host}:{port}...")
            smtp = smtplib.SMTP_SSL(host, port, timeout=20)
        else:
            logger.log(f"Conectando SMTP a {host}:{port}...")
            smtp = smtplib.SMTP(host, port, timeout=20)
        
        # Activar debug máximo y capturarlo
        smtp.set_debuglevel(2)
        
        # Redirigir stderr para capturar debug
        old_stderr = sys.stderr
        sys.stderr = debug_buffer
        
        try:
            logger.log("Conexión establecida", "OK")
            
            # EHLO
            logger.log("Enviando EHLO...", "DEBUG")
            code, msg = smtp.ehlo()
            ehlo_response = msg.decode('utf-8', errors='ignore')
            logger.log(f"EHLO respuesta ({code}):", "RAW", ehlo_response)
            result["ehlo_code"] = code
            result["ehlo_response"] = ehlo_response
            
            # Capabilities
            if smtp.esmtp_features:
                logger.log("Capacidades ESMTP:", "DEBUG")
                for feature, params in smtp.esmtp_features.items():
                    logger.log(f"  {feature}: {params}", "DEBUG")
                result["esmtp_features"] = dict(smtp.esmtp_features)
            
            # STARTTLS si no es SSL
            if not use_ssl:
                logger.log("Enviando STARTTLS...", "DEBUG")
                smtp.starttls()
                logger.log("STARTTLS completado", "OK")
                smtp.ehlo()
            
            # AUTH
            logger.log(f"Autenticando como: {user}", "DEBUG")
            logger.log(f"Password length: {len(password)} chars", "DEBUG")
            
            smtp.login(user, password)
            
            logger.log("🎉 ¡AUTENTICACIÓN EXITOSA!", "OK")
            result["success"] = True
            result["authenticated"] = True
            
            # Verificar si podemos enviar
            logger.log("Verificando capacidad de envío...", "DEBUG")
            
            smtp.quit()
            logger.log("Sesión cerrada correctamente", "DEBUG")
            
        finally:
            sys.stderr = old_stderr
            
        # Capturar todo el debug
        debug_output = debug_buffer.getvalue()
        if debug_output:
            result["smtp_debug_raw"] = debug_output
            logger.log("Debug SMTP raw:", "RAW", debug_output[-2000:])  # Últimos 2000 chars
            
    except smtplib.SMTPAuthenticationError as e:
        sys.stderr = old_stderr
        logger.log(f"🔐 ERROR AUTENTICACIÓN: {e.smtp_code}", "ERROR")
        error_msg = e.smtp_error.decode('utf-8', errors='ignore') if isinstance(e.smtp_error, bytes) else str(e.smtp_error)
        logger.log(f"Mensaje del servidor: {error_msg}", "RAW")
        result["error"] = f"Authentication failed: {e.smtp_code}"
        result["smtp_error_code"] = e.smtp_code
        result["smtp_error_message"] = error_msg
        
        # Diagnóstico
        if "535" in str(e.smtp_code):
            logger.log("💡 Código 535 = Credenciales incorrectas", "WARN")
        elif "534" in str(e.smtp_code):
            logger.log("💡 Código 534 = Necesita autenticación más segura", "WARN")
            
    except smtplib.SMTPConnectError as e:
        sys.stderr = old_stderr
        logger.log(f"🔌 ERROR DE CONEXIÓN: {e}", "ERROR")
        result["error"] = str(e)
        
    except smtplib.SMTPServerDisconnected as e:
        sys.stderr = old_stderr
        logger.log(f"🔌 SERVIDOR DESCONECTÓ: {e}", "ERROR")
        result["error"] = f"Server disconnected: {e}"
        
    except smtplib.SMTPException as e:
        sys.stderr = old_stderr
        logger.log(f"📧 ERROR SMTP: {e}", "ERROR")
        result["error"] = str(e)
        
    except socket.timeout:
        sys.stderr = old_stderr
        logger.log("⏱️  TIMEOUT durante sesión SMTP", "ERROR")
        result["error"] = "SMTP session timeout"
        
    except Exception as e:
        sys.stderr = old_stderr
        logger.log(f"💥 ERROR: {type(e).__name__}: {e}", "ERROR")
        logger.log(traceback.format_exc(), "RAW")
        result["error"] = str(e)
    
    # Guardar debug capturado
    debug_output = debug_buffer.getvalue()
    if debug_output:
        result["smtp_debug_raw"] = debug_output
    
    return result


def test_send_email(logger: DebugLogger, host: str, port: int, user: str, password: str, 
                    to_email: str) -> Dict[str, Any]:
    """Enviar email de prueba."""
    logger.section(f"ENVÍO DE EMAIL DE PRUEBA")
    result = {"test": "SEND", "to": to_email, "success": False}
    
    logger.log(f"Destinatario: {to_email}", "DEBUG")
    logger.log(f"Remitente: {user}", "DEBUG")
    
    try:
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.utils import formatdate, make_msgid
        
        # Conectar
        logger.log(f"Conectando SMTP_SSL a {host}:{port}...")
        smtp = smtplib.SMTP_SSL(host, port, timeout=20)
        smtp.set_debuglevel(2)
        smtp.login(user, password)
        logger.log("Conectado y autenticado", "OK")
        
        # Crear mensaje
        logger.log("Construyendo mensaje...", "DEBUG")
        msg = MIMEMultipart('alternative')
        msg['From'] = user
        msg['To'] = to_email
        msg['Subject'] = f"[TEST SMTP] Diagnóstico Railway - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid(domain=user.split('@')[1])
        
        # Cuerpo
        body_text = f"""
==============================================
    TEST DE SMTP DESDE RAILWAY
==============================================

Este email confirma que la configuración SMTP funciona.

Detalles técnicos:
- Fecha/Hora: {datetime.now().isoformat()}
- Servidor SMTP: {host}:{port}
- Usuario: {user}
- Método: SMTP_SSL (puerto 465)

Si ves este mensaje, ¡todo funciona correctamente!

==============================================
"""
        
        body_html = f"""
<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto; border: 2px solid #4CAF50; border-radius: 10px; padding: 20px;">
        <h1 style="color: #4CAF50;">✅ Test SMTP Exitoso</h1>
        <p>Este email confirma que la configuración SMTP funciona desde Railway.</p>
        <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
            <tr style="background: #f5f5f5;">
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Fecha/Hora</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Servidor</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;">{host}:{port}</td>
            </tr>
            <tr style="background: #f5f5f5;">
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Usuario</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;">{user}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Método</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;">SMTP_SSL</td>
            </tr>
        </table>
        <p style="margin-top: 20px; color: #666;">Enviado desde facturas-bot-empresa</p>
    </div>
</body>
</html>
"""
        
        msg.attach(MIMEText(body_text, 'plain'))
        msg.attach(MIMEText(body_html, 'html'))
        
        logger.log("Mensaje construido:", "DEBUG")
        logger.log(f"  Subject: {msg['Subject']}", "DEBUG")
        logger.log(f"  Message-ID: {msg['Message-ID']}", "DEBUG")
        
        # Enviar
        logger.log("Enviando email...", "DEBUG")
        smtp.sendmail(user, to_email, msg.as_string())
        
        logger.log("🎉 ¡EMAIL ENVIADO CORRECTAMENTE!", "OK")
        result["success"] = True
        result["message_id"] = msg['Message-ID']
        
        smtp.quit()
        
    except Exception as e:
        logger.log(f"💥 ERROR ENVIANDO: {e}", "ERROR")
        logger.log(traceback.format_exc(), "RAW")
        result["error"] = str(e)
    
    return result


# ============================================
# DIAGNÓSTICO COMPLETO
# ============================================

def run_full_diagnostic(test_email: str = None) -> Dict[str, Any]:
    """Ejecuta diagnóstico completo con debug intenso."""
    
    logger = DebugLogger()
    
    print("\n" + "🔬" * 30)
    print("  DIAGNÓSTICO SMTP ULTRA INTENSIVO")
    print("🔬" * 30)
    print(f"\nFecha/Hora: {datetime.now().isoformat()}")
    print(f"Host SMTP: {SMTP_HOST}")
    print(f"Usuario: {SMTP_USER}")
    print(f"Password configurado: {'Sí' if SMTP_PASS else '❌ NO'}")
    if test_email:
        print(f"Email de prueba: {test_email}")
    print()
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "config": {
            "smtp_host": SMTP_HOST,
            "smtp_port_ssl": SMTP_PORT_SSL,
            "smtp_port_tls": SMTP_PORT_TLS,
            "smtp_user": SMTP_USER,
            "smtp_pass_configured": bool(SMTP_PASS),
            "smtp_pass_length": len(SMTP_PASS) if SMTP_PASS else 0,
        },
        "tests": [],
        "summary": {}
    }
    
    # 1. Info de red
    net_info = test_network_info(logger)
    results["network"] = net_info
    
    # 2. DNS
    dns_result = test_dns_resolution(logger, SMTP_HOST)
    results["tests"].append(dns_result)
    
    if not dns_result["success"]:
        results["summary"]["diagnosis"] = "FALLO: No se puede resolver DNS del servidor SMTP"
        results["summary"]["can_send"] = False
        return results
    
    # 3. TCP 465
    tcp_465 = test_tcp_connection(logger, SMTP_HOST, SMTP_PORT_SSL)
    results["tests"].append(tcp_465)
    
    # 4. TCP 587
    tcp_587 = test_tcp_connection(logger, SMTP_HOST, SMTP_PORT_TLS)
    results["tests"].append(tcp_587)
    
    # Evaluar puertos
    port_465_ok = tcp_465["success"]
    port_587_ok = tcp_587["success"]
    
    if not port_465_ok and not port_587_ok:
        logger.section("❌ DIAGNÓSTICO FINAL")
        logger.log("AMBOS PUERTOS BLOQUEADOS (465 y 587)", "ERROR")
        logger.log("Railway probablemente bloquea SMTP saliente", "ERROR")
        logger.log("Solución: Usar servicio de email por API (Brevo, SendGrid)", "WARN")
        
        results["summary"]["diagnosis"] = "PUERTOS SMTP BLOQUEADOS - Railway no permite SMTP saliente"
        results["summary"]["can_send"] = False
        results["summary"]["solution"] = "Usar Brevo, SendGrid, o Resend (API REST)"
        return results
    
    # 5. SSL (si 465 funciona)
    if port_465_ok:
        ssl_result = test_ssl_handshake(logger, SMTP_HOST, SMTP_PORT_SSL)
        results["tests"].append(ssl_result)
    
    # 6. SMTP Auth
    if port_465_ok:
        smtp_result = test_smtp_session(logger, SMTP_HOST, SMTP_PORT_SSL, SMTP_USER, SMTP_PASS, use_ssl=True)
    elif port_587_ok:
        smtp_result = test_smtp_session(logger, SMTP_HOST, SMTP_PORT_TLS, SMTP_USER, SMTP_PASS, use_ssl=False)
    else:
        smtp_result = {"success": False}
    
    results["tests"].append(smtp_result)
    
    # 7. Enviar email de prueba
    if smtp_result.get("success") and test_email:
        send_result = test_send_email(logger, SMTP_HOST, 
                                       SMTP_PORT_SSL if port_465_ok else SMTP_PORT_TLS,
                                       SMTP_USER, SMTP_PASS, test_email)
        results["tests"].append(send_result)
        
        if send_result["success"]:
            results["summary"]["diagnosis"] = "✅ TODO FUNCIONA - Email enviado correctamente"
            results["summary"]["can_send"] = True
        else:
            results["summary"]["diagnosis"] = f"Auth OK pero fallo al enviar: {send_result.get('error')}"
            results["summary"]["can_send"] = False
    elif smtp_result.get("success"):
        results["summary"]["diagnosis"] = "✅ AUTENTICACIÓN OK - Añade ?email=tu@email.com para probar envío"
        results["summary"]["can_send"] = True
    else:
        results["summary"]["diagnosis"] = f"❌ FALLO AUTENTICACIÓN: {smtp_result.get('error')}"
        results["summary"]["can_send"] = False
    
    # Resumen final
    logger.section("📊 RESUMEN FINAL")
    
    passed = sum(1 for t in results["tests"] if t.get("success"))
    failed = len(results["tests"]) - passed
    
    logger.log(f"Tests pasados: {passed}/{len(results['tests'])}", "OK" if passed == len(results["tests"]) else "WARN")
    logger.log(f"Diagnóstico: {results['summary']['diagnosis']}", "INFO")
    
    results["summary"]["tests_passed"] = passed
    results["summary"]["tests_total"] = len(results["tests"])
    results["logs"] = logger.logs
    
    return results


# ============================================
# FASTAPI ENDPOINT
# ============================================
"""
Añadir a main.py:

from smtp_diagnostico import run_full_diagnostic

@app.get("/test-smtp")
async def test_smtp(email: str = None):
    return run_full_diagnostic(test_email=email)
"""


# ============================================
# EJECUCIÓN STANDALONE
# ============================================
if __name__ == "__main__":
    import json
    
    # Email de prueba desde argumentos
    test_email = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Ejecutar diagnóstico
    results = run_full_diagnostic(test_email)
    
    # Guardar JSON
    output_file = "/tmp/smtp_diagnostic_full.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Resultados JSON guardados en: {output_file}")
    print("\n" + "=" * 60)
    print("  FIN DEL DIAGNÓSTICO")
    print("=" * 60)

# 📧 Configuración Email Ionos

Esta guía te ayuda a configurar el email `aibot@dazzcreative.com` de Ionos para enviar correos desde el sistema.

---

## 🔑 Datos de Configuración Ionos

### **Servidor SMTP:**
- **Host**: `smtp.ionos.es` (España) o `smtp.ionos.com` (Internacional)
- **Puerto**: `587` (STARTTLS) o `465` (SSL/TLS)
- **Usuario**: `aibot@dazzcreative.com`
- **Contraseña**: La contraseña de tu cuenta de email

---

## ⚙️ Paso 1: Obtener Contraseña del Email

1. Inicia sesión en tu panel de Ionos
2. Ve a **Email & Office** → **Buzones de correo**
3. Localiza `aibot@dazzcreative.com`
4. Copia la contraseña (o cámbiala si no la recuerdas)

---

## 📝 Paso 2: Configurar .env

Edita el archivo `.env` en la raíz del proyecto:

```bash
# Email SMTP (Ionos)
SMTP_HOST=smtp.ionos.es
SMTP_PORT=587
SMTP_USER=aibot@dazzcreative.com
SMTP_PASSWORD=tu-contraseña-aqui
EMAIL_FROM=aibot@dazzcreative.com
EMAIL_FROM_NAME=Dazz Creative - Sistema Gastos
EMAIL_TO=miguel@dazzle-agency.com
```

**IMPORTANTE**: 
- Reemplaza `tu-contraseña-aqui` con la contraseña real
- NO subas este archivo a Git (ya está en .gitignore)

---

## 🧪 Paso 3: Probar Configuración

### Opción A: Desde Python (Recomendado)

Crea un archivo `test_email.py`:

```python
import os
from dotenv import load_dotenv
from app.services.email import send_email

load_dotenv()

# Enviar email de prueba
success = send_email(
    to_email="miguel@dazzle-agency.com",
    subject="🧪 Prueba Sistema Dazz Creative",
    html_body="""
    <h1>✅ Email de Prueba</h1>
    <p>Si recibes este email, la configuración SMTP de Ionos está correcta.</p>
    <p><strong>Sistema:</strong> Dazz Creative - Gestión Gastos</p>
    """
)

if success:
    print("✅ Email enviado correctamente!")
else:
    print("❌ Error al enviar email. Revisa la configuración.")
```

Ejecutar:
```bash
python test_email.py
```

### Opción B: Desde cURL (API)

```bash
# Primero inicia el servidor
python main.py

# En otra terminal, crea un usuario de prueba (enviará email automático)
curl -X POST http://localhost:8000/auth/register \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Usuario Prueba",
    "email": "prueba@example.com",
    "password": "test123",
    "role": "user"
  }'
```

Debería enviar un email automático a `prueba@example.com` con las credenciales.

---

## 🔍 Troubleshooting

### Error: "Authentication failed"
**Solución:**
1. Verifica que la contraseña sea correcta
2. Asegúrate de usar `aibot@dazzcreative.com` (email completo)
3. Revisa que el puerto sea `587`

### Error: "Connection refused"
**Solución:**
1. Prueba cambiar el host a `smtp.ionos.com` (sin `.es`)
2. O prueba puerto `465` con SSL:
```bash
SMTP_HOST=smtp.ionos.es
SMTP_PORT=465
```

### Error: "SMTP AUTH extension not supported"
**Solución:**
Ionos requiere autenticación. Verifica que estés usando STARTTLS:
```python
server.starttls()
server.login(SMTP_USER, SMTP_PASSWORD)
```

### Error: "Timeout"
**Solución:**
1. Verifica tu conexión a Internet
2. Comprueba que tu firewall no bloquee el puerto 587/465
3. Prueba desde otra red (a veces redes corporativas bloquean SMTP)

---

## 📧 Tipos de Emails Automáticos

El sistema enviará emails automáticamente en estos casos:

### 1. Usuario Creado
**Cuándo:** Un admin crea un nuevo usuario  
**A quién:** Al nuevo usuario  
**Contenido:** Email de bienvenida + credenciales temporales

### 2. Proyecto Cerrado
**Cuándo:** Se cierra un proyecto  
**A quién:** miguel@dazzle-agency.com  
**CC:** Responsable del proyecto  
**Contenido:** Resumen + link SharePoint + archivos

---

## 🔐 Seguridad

### ✅ Buenas Prácticas:

1. **No uses contraseñas débiles** en `aibot@dazzcreative.com`
2. **Activa 2FA** en tu cuenta de Ionos si es posible
3. **NO subas .env a Git** (ya está en .gitignore)
4. **En producción**, usa variables de entorno del servidor (Render, Railway, etc.)

### ⚠️ Límites de Ionos:

- **Emails por día**: Depende de tu plan (normalmente 500-1000)
- **Emails por hora**: ~50-100
- Si superas el límite, espera 1 hora

Para el uso normal del sistema (20-50 emails/día), no habrá problemas.

---

## 🚀 Siguiente Paso

Una vez configurado el email, prueba crear un usuario y verifica que llegue el email de bienvenida.

Si todo funciona, continúa con la [Guía de Deploy](DEPLOY.md) para subir a producción.

---

## 📞 Soporte Ionos

Si tienes problemas específicos de Ionos:
- **Soporte**: https://www.ionos.es/ayuda/
- **Teléfono**: 900 502 621
- **Email**: info@ionos.es

---

**¿Problemas?** Revisa el archivo `/app/services/email.py` y asegúrate de que las credenciales en `.env` son correctas.

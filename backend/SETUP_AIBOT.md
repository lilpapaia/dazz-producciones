# 🤖 Configuración Completa - aibot@dazzcreative.com

Esta guía configura el sistema con `aibot@dazzcreative.com` como:
1. **Usuario administrador** del sistema
2. **Email de envío** para notificaciones

---

## 🎯 CONFIGURACIÓN COMPLETA (10 minutos)

### **Paso 1: Configurar Variables de Entorno**

Edita `.env` y configura:

```bash
# Claude AI (OBLIGATORIO)
ANTHROPIC_API_KEY=sk-ant-api03-TU_API_KEY_AQUI

# Email Ionos (OBLIGATORIO)
SMTP_HOST=smtp.ionos.es
SMTP_PORT=587
SMTP_USER=aibot@dazzcreative.com
SMTP_PASSWORD=TU_CONTRASEÑA_IONOS
EMAIL_FROM=aibot@dazzcreative.com
EMAIL_FROM_NAME=Dazz Creative - Sistema Gastos
EMAIL_TO=miguel@dazzle-agency.com

# Seguridad (Cambiar en producción)
SECRET_KEY=tu-secret-key-super-segura-cambiala-en-produccion
```

### **Paso 2: Iniciar Servidor**

```bash
# Linux/Mac
./start.sh

# Windows
start.bat
```

### **Paso 3: Crear Usuario aibot (Admin)**

Abre http://localhost:8000/docs y ejecuta:

**Endpoint:** `POST /auth/register-first-admin`

**Body:**
```json
{
  "name": "AI Bot - Dazz Creative",
  "email": "aibot@dazzcreative.com",
  "password": "elige-contraseña-muy-segura-aqui",
  "role": "admin"
}
```

Click **Execute**

✅ Usuario `aibot@dazzcreative.com` creado como **ADMIN**

---

## 🔑 **Paso 4: Login como aibot**

**Endpoint:** `POST /auth/login`

**Body:**
```json
{
  "email": "aibot@dazzcreative.com",
  "password": "tu-contraseña-aqui"
}
```

Copia el `access_token` de la respuesta.

---

## 🔒 **Paso 5: Autorizar en Swagger**

1. Click botón verde **"Authorize"** (arriba derecha)
2. Escribe: `Bearer TU_TOKEN_AQUI`
3. Click **Authorize**

---

## 👤 **Paso 6: Crear Usuario Miguel (Admin)**

**Endpoint:** `POST /auth/register`

**Body:**
```json
{
  "name": "Miguel",
  "email": "miguel@dazzle-agency.com",
  "password": "contraseña-segura-miguel",
  "role": "admin"
}
```

✅ Se enviará email automático a miguel@dazzle-agency.com con las credenciales

---

## 👥 **Paso 7: Crear Usuarios del Equipo**

Ahora puedes crear usuarios (Julieta, Antonio, etc.):

**Endpoint:** `POST /auth/register`

**Body:**
```json
{
  "name": "Julieta",
  "email": "julieta@dazzle-agency.com",
  "password": "julieta123",
  "role": "user"
}
```

✅ Cada usuario recibirá email automático con sus credenciales

---

## 📧 **Emails Automáticos que Enviará el Sistema**

### 1. Nuevo Usuario Creado
```
De: aibot@dazzcreative.com
Para: usuario-nuevo@dazzle-agency.com
Asunto: Tu cuenta en Dazz Creative - Sistema Gastos

Contenido:
- Bienvenida
- Email de acceso
- Contraseña temporal
- Link para iniciar sesión
```

### 2. Proyecto Cerrado
```
De: aibot@dazzcreative.com
Para: miguel@dazzle-agency.com
CC: responsable-proyecto@dazzle-agency.com
Asunto: [Producción Cerrada] Nombre del Proyecto

Contenido:
- Resumen del proyecto
- Total de tickets
- Importe total
- Link a SharePoint con Excel + tickets
```

---

## 🎯 **Estructura de Usuarios Recomendada**

| Email | Nombre | Rol | Uso |
|-------|--------|-----|-----|
| `aibot@dazzcreative.com` | AI Bot | Admin | Sistema / Emails automáticos |
| `miguel@dazzle-agency.com` | Miguel | Admin | Gestión general |
| `tu-email@dazzle-agency.com` | Tu nombre | Admin | Gestión general |
| `julieta@dazzle-agency.com` | Julieta | User | Gestión producciones |
| `antonio@dazzle-agency.com` | Antonio | User | Gestión producciones |

---

## ✅ **Verificación Final**

### Test 1: Email Funciona
```bash
# Crear usuario de prueba
curl -X POST http://localhost:8000/auth/register \
  -H "Authorization: Bearer TU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "test123",
    "role": "user"
  }'
```

Verifica que llegue email a `test@example.com`

### Test 2: Crear Proyecto
```bash
curl -X POST http://localhost:8000/projects \
  -H "Authorization: Bearer TU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "year": "2026",
    "creative_code": "OC-PROD202600001",
    "company": "DAZZ CREATIVE",
    "responsible": "MIGUEL",
    "invoice_type": "PRODUCCION2026",
    "description": "Proyecto de prueba"
  }'
```

### Test 3: Subir Ticket con IA
```bash
curl -X POST http://localhost:8000/tickets/1/upload \
  -H "Authorization: Bearer TU_TOKEN" \
  -F "file=@/ruta/a/factura.jpg"
```

---

## 🔐 **Seguridad**

### ⚠️ IMPORTANTE:

1. **Cambia SECRET_KEY** en producción:
```bash
# Generar nueva key segura
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

2. **Usa contraseñas fuertes** para todos los usuarios

3. **NO subas .env a Git** (ya está en .gitignore)

4. **Activa 2FA** en aibot@dazzcreative.com (Ionos)

---

## 📊 **Límites de Uso**

### Ionos Email:
- **500-1000 emails/día** (depende del plan)
- **50-100 emails/hora**

Para uso normal (20-50 emails/día), no hay problema.

### Claude AI:
- **200 tickets/mes** → ~5€
- **1000 tickets/mes** → ~25€

---

## 🚀 **Siguiente Paso**

Una vez todo configurado:

1. ✅ Crea todos los usuarios del equipo
2. ✅ Cada uno recibe su email con credenciales
3. ✅ Pueden cambiar su contraseña en primer login
4. ✅ ¡Sistema listo para usar!

---

## 🐛 **Troubleshooting**

### Error: "Could not send email"
→ Revisa configuración SMTP en `.env`
→ Verifica contraseña de aibot@dazzcreative.com
→ Lee guía completa: [IONOS_EMAIL_SETUP.md](IONOS_EMAIL_SETUP.md)

### Error: "Authentication failed" (SMTP)
→ Usa email completo: `aibot@dazzcreative.com`
→ Prueba host alternativo: `smtp.ionos.com`

### Error: "Users already exist"
→ Solo puedes usar `/register-first-admin` si la BD está vacía
→ Usa `/auth/register` para crear más usuarios (requiere estar logueado como admin)

---

## 📞 **Soporte**

**Dudas sistema:** miguel@dazzle-agency.com  
**Problemas Ionos:** 900 502 621  
**Problemas Claude:** console.anthropic.com/support

---

**¡Sistema configurado y listo!** 🎉

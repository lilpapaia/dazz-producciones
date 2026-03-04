# ⚡ INICIO RÁPIDO - 5 MINUTOS

## 🎯 Paso 1: Obtener Claude API Key

1. Ve a: https://console.anthropic.com
2. Regístrate o inicia sesión
3. Ve a "API Keys"
4. Click "Create Key"
5. Copia la key (empieza con `sk-ant-api03-...`)

## 🚀 Paso 2: Iniciar el Backend

### Linux/Mac:
```bash
cd dazz-producciones-backend
./start.sh
```

### Windows:
```bash
cd dazz-producciones-backend
start.bat
```

El script te pedirá:
1. Añadir tu ANTHROPIC_API_KEY al archivo `.env`
2. Configurar email Ionos (opcional para pruebas)
3. Presionar ENTER para continuar
4. El servidor se iniciará automáticamente

## 🧪 Paso 3: Probar la API

Abre tu navegador en:
- **Documentación interactiva**: http://localhost:8000/docs

## 👤 Paso 4: Crear primer usuario (aibot o admin)

En la documentación (http://localhost:8000/docs):

### Opción A: Con aibot@dazzcreative.com (Recomendado)
```json
{
  "name": "AI Bot - Dazz Creative",
  "email": "aibot@dazzcreative.com",
  "password": "contraseña-muy-segura",
  "role": "admin"
}
```

### Opción B: Con Miguel directamente
```json
{
  "name": "Miguel",
  "email": "miguel@dazzle-agency.com",
  "password": "admin123",
  "role": "admin"
}
```

**Endpoint:** `POST /auth/register-first-admin`

## 🔑 Paso 5: Login

1. Busca `POST /auth/login`
2. Click "Try it out"
3. Rellena con tu email y contraseña
4. Click "Execute"
5. Copia el `access_token` de la respuesta

## 🔒 Paso 6: Autorizar en Swagger

1. Click en el botón verde "Authorize" (arriba a la derecha)
2. Escribe: `Bearer TU_TOKEN_AQUÍ`
3. Click "Authorize"
4. ¡Ya puedes usar todos los endpoints!

## ✅ Paso 7: Crear proyecto de prueba

1. Busca `POST /projects`
2. Click "Try it out"
3. Rellena:
```json
{
  "year": "2026",
  "creative_code": "OC-PROD202600001",
  "company": "DIGITAL ADVERTISING SOCIAL SERVICES SL",
  "responsible": "JULIETA",
  "invoice_type": "PRODUCCION2026",
  "description": "Proyecto de prueba",
  "send_date": "2026-03-10"
}
```
4. Click "Execute"
5. Copia el `id` del proyecto creado

## 📸 Paso 8: Subir un ticket con IA

1. Busca `POST /tickets/{project_id}/upload`
2. Click "Try it out"
3. En `project_id` pon el ID del paso anterior
4. Click "Choose File" y selecciona una imagen de factura
5. Click "Execute"
6. ¡La IA extraerá automáticamente todos los datos!

---

## 🎉 ¡LISTO!

Ya tienes el backend funcionando con:
- ✅ Autenticación
- ✅ Gestión de proyectos
- ✅ Extracción automática con IA
- ✅ API completa

---

## 📚 Configuración Completa

Para configuración completa con aibot@dazzcreative.com y emails automáticos:
- **Guía completa:** [SETUP_AIBOT.md](SETUP_AIBOT.md)
- **Configuración email:** [IONOS_EMAIL_SETUP.md](IONOS_EMAIL_SETUP.md)
- **Documentación:** [README.md](README.md)

---

## 🐛 Troubleshooting

**¿Problemas?** Revisa el archivo `.env` y asegúrate de que tu `ANTHROPIC_API_KEY` es correcta.

**Sin email configurado:** El sistema funciona perfectamente, solo no enviará notificaciones automáticas.

**Ejemplos completos:** Lee [API_EXAMPLES.md](API_EXAMPLES.md) para ver ejemplos cURL de todas las operaciones.

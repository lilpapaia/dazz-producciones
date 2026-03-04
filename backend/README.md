# Dazz Creative - Sistema Gestión Gastos

Backend API para gestión de proyectos y tickets/facturas con extracción automática mediante Claude AI.

## 🚀 Características

- ✅ **Autenticación JWT** con roles (Admin/Usuario)
- ✅ **Extracción automática de datos** con Claude AI
- ✅ **Gestión de proyectos** (crear, editar, cerrar, reabrir)
- ✅ **Gestión de tickets** (subir, extraer, revisar, editar)
- ✅ **Gestión de usuarios** (solo admins)
- ✅ **Base de datos SQLite** (fácil de migrar a PostgreSQL)
- ✅ **API RESTful** completa

## 📋 Requisitos

- Python 3.9+
- Claude API Key (obtener en console.anthropic.com)

## 🔧 Instalación

### 1. Clonar y entrar al directorio

```bash
cd dazz-producciones-backend
```

### 2. Crear entorno virtual

```bash
python -m venv venv

# Activar (Linux/Mac)
source venv/bin/activate

# Activar (Windows)
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
```

Editar `.env` y completar:

```env
# OBLIGATORIO: Claude API Key
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# Opcional: cambiar en producción
SECRET_KEY=your-secret-key-change-this-in-production

# Email (FASE 2)
SMTP_USER=noreply@dazzle-agency.com
SMTP_PASSWORD=your-app-password
```

### 5. Iniciar servidor

```bash
python main.py
```

O con uvicorn directamente:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📚 Documentación API

Una vez iniciado el servidor, accede a:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🎯 Primeros Pasos

### 1. Crear primer usuario admin

```bash
POST /auth/register-first-admin
{
  "name": "Miguel",
  "email": "miguel@dazzle-agency.com",
  "password": "tu-contraseña-segura"
}
```

Este endpoint **solo funciona si no hay usuarios** en la base de datos.

### 2. Login

```bash
POST /auth/login
{
  "email": "miguel@dazzle-agency.com",
  "password": "tu-contraseña"
}
```

Respuesta:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJh...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "name": "Miguel",
    "email": "miguel@dazzle-agency.com",
    "role": "admin"
  }
}
```

### 3. Usar el token

Incluir en todas las peticiones protegidas:

```bash
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJh...
```

## 🔑 Endpoints Principales

### Autenticación
- `POST /auth/register-first-admin` - Crear primer admin
- `POST /auth/login` - Login
- `POST /auth/register` - Crear usuario (solo admin)

### Proyectos
- `POST /projects` - Crear proyecto
- `GET /projects` - Listar proyectos
- `GET /projects/{id}` - Ver proyecto
- `PUT /projects/{id}` - Actualizar proyecto
- `POST /projects/{id}/close` - Cerrar proyecto
- `POST /projects/{id}/reopen` - Reabrir proyecto (admin)
- `DELETE /projects/{id}` - Eliminar proyecto (admin)

### Tickets
- `POST /tickets/extract` - Extraer datos (preview)
- `POST /tickets/{project_id}/upload` - Subir ticket + auto-extraer
- `GET /tickets/{project_id}/tickets` - Listar tickets del proyecto
- `PUT /tickets/{ticket_id}` - Actualizar ticket
- `DELETE /tickets/{ticket_id}` - Eliminar ticket

### Usuarios (Admin)
- `GET /users` - Listar usuarios
- `GET /users/{id}` - Ver usuario
- `PUT /users/{id}` - Actualizar usuario
- `DELETE /users/{id}` - Eliminar usuario

## 📊 Estructura del Proyecto

```
dazz-producciones-backend/
├── app/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py      # Modelos SQLAlchemy
│   │   └── schemas.py       # Esquemas Pydantic
│   ├── routes/
│   │   ├── auth.py          # Rutas autenticación
│   │   ├── projects.py      # Rutas proyectos
│   │   ├── tickets.py       # Rutas tickets
│   │   └── users.py         # Rutas usuarios
│   └── services/
│       ├── auth.py          # Lógica JWT y permisos
│       └── claude_ai.py     # Extracción con Claude
├── config/
│   └── database.py          # Configuración DB
├── uploads/                 # Archivos subidos
├── .env                     # Variables de entorno
├── .env.example             # Template variables
├── main.py                  # Aplicación principal
├── requirements.txt         # Dependencias
└── README.md               # Esta documentación
```

## 🧪 Testing con cURL

### Crear primer admin
```bash
curl -X POST http://localhost:8000/auth/register-first-admin \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Miguel",
    "email": "miguel@dazzle-agency.com",
    "password": "admin123",
    "role": "admin"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "miguel@dazzle-agency.com",
    "password": "admin123"
  }'
```

### Crear proyecto (con token)
```bash
curl -X POST http://localhost:8000/projects \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "year": "2026",
    "creative_code": "OC-PROD202600001",
    "company": "DIGITAL ADVERTISING SOCIAL SERVICES SL",
    "responsible": "JULIETA",
    "invoice_type": "PRODUCCION2026",
    "description": "Proyecto de prueba"
  }'
```

### Subir ticket con extracción IA
```bash
curl -X POST http://localhost:8000/tickets/1/upload \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "file=@/path/to/ticket.jpg"
```

## 🚀 Deploy en Producción

### Render.com (Recomendado)

1. Crear cuenta en Render.com
2. New Web Service → Conectar repositorio GitHub
3. Configurar:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Environment Variables:
   - `ANTHROPIC_API_KEY`
   - `SECRET_KEY`
   - `ENVIRONMENT=production`
5. Deploy automático

## 🔒 Seguridad

- ✅ Contraseñas hasheadas con bcrypt
- ✅ JWT con expiración (7 días por defecto)
- ✅ Validación de permisos por rol
- ✅ Validación de archivos (solo JPG, PNG, PDF)
- ⚠️ Cambiar SECRET_KEY en producción
- ⚠️ Configurar CORS específico en producción

## 📝 Notas Importantes

### Claude AI
- Requiere API key válida
- Modelo usado: `claude-sonnet-4-20250514`
- Coste aprox: ~5€/mes (200 tickets)
- Precisión esperada: ~95-98%

### Base de Datos
- SQLite por defecto (dev)
- Migrar a PostgreSQL en producción
- Cambiar `DATABASE_URL` en `.env`

### Archivos
- Se guardan en `/uploads/project_{id}/`
- No se eliminan al borrar tickets (manual)
- Configurar backup en producción

## 🐛 Troubleshooting

### Error: "ANTHROPIC_API_KEY not found"
→ Crear archivo `.env` y añadir tu API key

### Error: "Could not validate credentials"
→ Token expirado, hacer login nuevamente

### Error: "Not enough permissions"
→ Usuario no tiene permisos (requiere admin)

## 📧 Soporte

Para dudas o problemas: miguel@dazzle-agency.com

---

**Desarrollado para Dazz Creative** 🎬

# 🧪 Ejemplos de Peticiones API

Este archivo contiene ejemplos de todas las peticiones principales de la API.

**IMPORTANTE**: Reemplaza `YOUR_TOKEN_HERE` con tu token JWT real.

---

## 🔐 AUTENTICACIÓN

### Crear primer admin (solo funciona si DB está vacía)
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

Guarda el `access_token` de la respuesta para usarlo en las siguientes peticiones.

---

## 👥 USUARIOS (Solo Admin)

### Crear nuevo usuario
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Julieta",
    "email": "julieta@dazzle-agency.com",
    "password": "julieta123",
    "role": "user"
  }'
```

### Listar todos los usuarios
```bash
curl -X GET http://localhost:8000/users \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Ver un usuario específico
```bash
curl -X GET http://localhost:8000/users/1 \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Actualizar usuario
```bash
curl -X PUT http://localhost:8000/users/2 \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Julieta García",
    "email": "julieta@dazzle-agency.com",
    "password": "nueva-pass",
    "role": "user"
  }'
```

### Eliminar usuario
```bash
curl -X DELETE http://localhost:8000/users/2 \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## 📁 PROYECTOS

### Crear proyecto
```bash
curl -X POST http://localhost:8000/projects \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "year": "2026",
    "send_date": "2026-03-15",
    "creative_code": "OC-PROD202600164",
    "company": "DIGITAL ADVERTISING SOCIAL SERVICES SL",
    "responsible": "JULIETA",
    "invoice_type": "PRODUCCION2026",
    "description": "Carlos Mimet x Prada Beauty TikTok Content",
    "other_invoice_data": "3% MARGEN CARLOS MIMET",
    "client_oc": "7000958658",
    "client_data": "Transparence Consulting, Paris, France",
    "client_email": "aurelien@transparenceconsulting.com",
    "project_link": "https://dazzledazz.sharepoint.com/:f:/g/xxxxx"
  }'
```

### Listar todos los proyectos
```bash
curl -X GET http://localhost:8000/projects \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Ver proyecto específico
```bash
curl -X GET http://localhost:8000/projects/1 \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Actualizar proyecto
```bash
curl -X PUT http://localhost:8000/projects/1 \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Descripción actualizada"
  }'
```

### Cerrar proyecto
```bash
curl -X POST http://localhost:8000/projects/1/close \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Reabrir proyecto (solo admin)
```bash
curl -X POST http://localhost:8000/projects/1/reopen \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Eliminar proyecto (solo admin)
```bash
curl -X DELETE http://localhost:8000/projects/1 \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## 🎫 TICKETS

### Extraer datos (preview - no guarda)
```bash
curl -X POST http://localhost:8000/tickets/extract \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "file=@/ruta/a/tu/factura.jpg"
```

### Subir ticket + auto-extraer
```bash
curl -X POST http://localhost:8000/tickets/1/upload \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "file=@/ruta/a/tu/factura.jpg"
```

### Listar tickets de un proyecto
```bash
curl -X GET http://localhost:8000/tickets/1/tickets \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Actualizar ticket (correcciones manuales)
```bash
curl -X PUT http://localhost:8000/tickets/1 \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "MediaMarkt España",
    "base_amount": 195.04,
    "po_notes": "Material oficina para shooting",
    "invoice_status": "RECIBIDO",
    "payment_status": "PENDIENTE",
    "is_reviewed": true
  }'
```

### Eliminar ticket
```bash
curl -X DELETE http://localhost:8000/tickets/1 \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## 📊 Ejemplo de Flujo Completo

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"miguel@dazzle-agency.com","password":"admin123"}' \
  | jq -r '.access_token')

# 2. Crear proyecto
PROJECT_ID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "year": "2026",
    "creative_code": "OC-PROD202600001",
    "company": "DAZZ CREATIVE",
    "responsible": "MIGUEL",
    "invoice_type": "PRODUCCION2026",
    "description": "Proyecto de prueba"
  }' | jq -r '.id')

# 3. Subir ticket
curl -X POST http://localhost:8000/tickets/$PROJECT_ID/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@factura.jpg"

# 4. Ver tickets del proyecto
curl -X GET http://localhost:8000/tickets/$PROJECT_ID/tickets \
  -H "Authorization: Bearer $TOKEN"

# 5. Cerrar proyecto
curl -X POST http://localhost:8000/projects/$PROJECT_ID/close \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🔍 Health Check

```bash
curl -X GET http://localhost:8000/health
```

---

**Nota**: Todos estos ejemplos asumen que el servidor está corriendo en `http://localhost:8000`.
Si está en otro puerto o dominio, ajusta la URL en consecuencia.

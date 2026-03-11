# Memory - Contexto del Proyecto

## 🎯 Proyecto

**Nombre:** Dazz Producciones  
**Descripción:** Sistema gestión gastos con IA para productora audiovisual  
**Cliente:** Dazz Creative (productora Madrid)  
**Estado:** ✅ Producción activa - 314 deployments  
**GitHub:** https://github.com/lilpapaja/dazz-producciones (público)  
**Desarrollador:** Julio (lilpapaja) - Nivel junior, primera vez con Claude Code

---

## 🛠️ Stack Tecnológico

### Backend
- **Framework:** FastAPI 0.104.1
- **ORM:** SQLAlchemy 2.0.23
- **Base de datos:** 
  - Local: SQLite (`dazz_producciones.db`)
  - Producción: PostgreSQL (Railway)
- **IA:** Claude Sonnet 4 (Anthropic API)
- **Auth:** JWT (python-jose)
- **Emails:** Brevo API (Railway bloquea SMTP)
- **Storage:** Cloudinary (imágenes facturas)
- **Deploy:** Railway (auto-deploy desde GitHub)

### Frontend
- **Framework:** React 19.2 + Vite 7.3
- **Styling:** Tailwind CSS (theme: dark zinc/amber)
- **Routing:** React Router DOM
- **Charts:** Recharts (estadísticas)
- **Icons:** Lucide React
- **PWA:** vite-plugin-pwa (service workers, offline)
- **Compresión:** browser-image-compression
- **PDF:** jsPDF
- **Excel:** xlsx (lectura), backend genera con openpyxl
- **Deploy:** Vercel (auto-deploy desde GitHub)

### URLs Producción
- **Backend:** https://dazz-producciones-production.up.railway.app
- **Frontend:** https://dazz-producciones.vercel.app

---

## 🏗️ Arquitectura

### Estructura Backend
```
backend/
├── app/
│   ├── models/
│   │   ├── database.py       # SQLAlchemy models
│   │   └── schemas.py        # Pydantic schemas
│   ├── routes/
│   │   ├── auth.py          # Login, register, JWT
│   │   ├── projects.py      # CRUD proyectos + cierre
│   │   ├── tickets.py       # Upload, IA extracción
│   │   ├── statistics.py    # Stats + IVA extranjero
│   │   ├── users.py         # Gestión usuarios
│   │   └── companies.py     # Multi-tenant
│   └── services/
│       ├── claude_ai.py              # Extracción IA
│       ├── email.py                  # Brevo API
│       ├── excel_generator.py        # BytesIO Excel
│       ├── exchange_rate.py          # Tasas cambio
│       └── geographic_classifier.py  # NACIONAL/UE/INT
├── config/
│   └── database.py          # Auto-detect SQLite/PostgreSQL
├── main.py                  # FastAPI app
└── railway.json             # Deploy config
```

### Estructura Frontend
```
frontend/
├── src/
│   ├── pages/
│   │   ├── Login.jsx
│   │   ├── Dashboard.jsx
│   │   ├── ProjectCreate.jsx, ProjectView.jsx
│   │   ├── UploadTickets.jsx      # Camera + compresión
│   │   ├── ReviewTicket.jsx
│   │   ├── ProjectCloseReview.jsx # Preview + emails
│   │   ├── Statistics.jsx         # 500+ líneas (refactor)
│   │   └── Users.jsx
│   ├── components/
│   │   ├── Navbar.jsx
│   │   ├── EmailChipsInput.jsx    # Selector emails
│   │   └── PWAComponents.jsx      # Update/install prompts
│   ├── context/
│   │   └── AuthContext.jsx
│   ├── services/
│   │   └── api.js                 # Axios calls
│   └── App.jsx
└── vite.config.js                 # PWA config
```

---

## 💡 Decisiones Arquitectónicas Clave

### 1. Claude Sonnet 4 para extracción automática
**Decisión:** Usar IA en vez de OCR tradicional  
**Razón:** Facturas variadas (formatos, idiomas), Claude entiende contexto  
**Resultado:** ~95% precisión, detecta moneda/país automático

### 2. Brevo API en vez de SMTP
**Decisión:** API REST HTTP en vez de SMTP tradicional  
**Razón:** Railway bloquea puerto 587/465 (SMTP)  
**Resultado:** Emails funcionan perfecto en Railway

### 3. BytesIO para Excel (sin filesystem)
**Decisión:** Generar Excel en memoria, NO guardar en disco  
**Razón:** Compatible cloud (Railway no persistente), más rápido  
**Resultado:** Compatible Railway/Render/Fly.io, sin basura

### 4. Multi-tenant con tabla companies
**Decisión:** Empresas como entidad separada + many-to-many con users  
**Razón:** Dazz tiene múltiples empresas legales, permisos granulares  
**Resultado:** ADMIN ve todo, BOSS solo su empresa, WORKER sus proyectos

### 5. PWA con cámara móvil
**Decisión:** `capture="environment"` en input file  
**Razón:** Escaneo facturas in-situ (restaurantes, tiendas)  
**Resultado:** App instalable, funciona offline, cámara directa

### 6. Compresión automática imágenes
**Decisión:** Comprimir >3MB automático antes upload  
**Razón:** Claude API límite 5MB, fotos móvil 6-8MB  
**Resultado:** Fotos móvil funcionan sin error

### 7. Dark theme zinc/amber
**Decisión:** Zinc 950 (negro) + amber 500 (dorado)  
**Razón:** Identidad visual Dazz, profesional, reduce fatiga  
**Resultado:** Diseño distintivo, branded

### 8. PostgreSQL auto-switch
**Decisión:** `database_config.py` detecta SQLite vs PostgreSQL  
**Razón:** Desarrollo fácil (SQLite), producción robusta (PostgreSQL)  
**Resultado:** Mismo código, dos entornos sin cambios

---

## 👥 Usuarios y Roles

### Roles Sistema
1. **ADMIN** (Miguel)
   - Ve TODO (todos proyectos, todas empresas)
   - CRUD usuarios, empresas, proyectos
   - Acceso estadísticas globales

2. **BOSS** (Julieta, Antonio)
   - Ve solo proyectos de SU empresa
   - Crea proyectos en su empresa
   - Cierra proyectos
   - Estadísticas filtradas su empresa

3. **WORKER** (empleados)
   - Ve solo SUS proyectos
   - Sube tickets
   - Revisa tickets
   - NO puede cerrar proyectos

### Usuarios Principales
- **Miguel:** miguel@dazzcreative.com (ADMIN)
- **Julieta:** julieta@dazzcreative.com (BOSS/WORKER)
- **Antonio:** antonio@dazzcreative.com (BOSS/WORKER)

---

## 📊 Empresas Activas

**Dazz Creative tiene múltiples empresas legales:**
1. DIGITAL ADVERTISING SOCIAL SERVICES SL
2. DAZZ CREATIVE AUDIOVISUAL SL
3. (Otras según CIF)

**Cada proyecto pertenece a UNA empresa** (`owner_company_id`)

---

## 🔑 Features Principales

### ✅ Implementadas (Producción)
1. **Gestión proyectos** - CRUD completo con 12 campos
2. **Upload tickets** - JPG/PNG/PDF + cámara móvil + compresión
3. **IA extracción** - Claude detecta: proveedor, fecha, importes, moneda, país
4. **Review tickets** - Corrección manual + lightbox imagen
5. **Cierre proyectos** - Preview Excel + selector emails + descarga + marca cerrado
6. **Estadísticas** - Gráficos Recharts + IVA extranjero reclamable + export PDF
7. **Multi-tenant** - Permisos por empresa (ADMIN/BOSS/WORKER)
8. **Auth JWT** - Login + refresh tokens + roles
9. **PWA** - Instalable + offline + cámara
10. **Email styled** - Dark theme Brevo branded

### ⏸️ Pendientes (Roadmap)
- Tests unitarios backend (0% coverage)
- Tests E2E frontend (Playwright)
- Refactorizar Statistics.jsx (500+ líneas)
- Optimizar queries N+1
- Code splitting frontend
- Push notifications PWA
- Dashboard analytics

---

## 🚨 Problemas Conocidos

### 1. Statistics.jsx muy grande
**Problema:** 500+ líneas, difícil mantener  
**Solución:** Refactorizar en componentes pequeños

### 2. Bundle size grande
**Problema:** Initial bundle ~350KB  
**Solución:** Lazy load rutas, separar Recharts

### 3. Sin tests
**Problema:** 0% coverage, deploys sin validación  
**Solución:** pytest backend + Playwright frontend

### 4. Queries potencialmente N+1
**Problema:** Cargar projects + tickets puede ser lento  
**Solución:** Auditar joinedload, índices PostgreSQL

---

## 📐 Estándares de Código

### Backend (Python)
- **Formato:** PEP 8, snake_case
- **Type hints:** Siempre en funciones públicas
- **Docstrings:** Funciones complejas y servicios
- **Error handling:** try/except con HTTPException
- **Validación:** Pydantic schemas + FastAPI

### Frontend (React)
- **Formato:** Prettier, camelCase
- **Componentes:** Functional components + hooks
- **Naming:** PascalCase componentes, camelCase funciones
- **Estado:** useState local, Context global (AuthContext)
- **Styling:** Tailwind utility classes inline

### Commits
- **Formato:** Conventional Commits (`feat:`, `fix:`, `refactor:`)
- **Scope:** `backend:`, `frontend:`, `docs:`
- **Descripción:** Español, imperativo, conciso

---

## 🎨 Design System

### Colores
- **Fondo:** `bg-zinc-950` (casi negro)
- **Cards:** `bg-zinc-900` (gris oscuro)
- **Bordes:** `border-zinc-800` / `border-zinc-700`
- **Texto:** `text-zinc-100` (blanco) / `text-zinc-400` (gris)
- **Primary:** `text-amber-500` (dorado), `hover:text-amber-600`
- **Success:** `text-green-400`
- **Error:** `text-red-400`
- **Info:** `text-blue-400`

### Tipografía
- **Títulos:** Bebas Neue (mayúsculas, tracking-wider)
- **Código:** IBM Plex Mono
- **Cuerpo:** System fonts

### Componentes
- **Buttons:** `rounded-sm` (esquinas suaves), `px-6 py-3`
- **Cards:** `border border-zinc-800 rounded-sm`
- **Inputs:** Dark zinc con focus amber
- **Modals:** Backdrop blur, zinc-900

---

## 🔄 Workflow Git

### Branches
- **main:** Producción (auto-deploy)
- **develop:** Desarrollo (opcional)
- **feature/*:** Features nuevas

### Deploy
- **Backend:** Railway auto-deploy desde main
- **Frontend:** Vercel auto-deploy desde main
- **Tiempo:** ~2-3 minutos total

---

## 📞 Contacto y Recursos

### Documentación
- **Técnica:** backend/DOCUMENTACION_COMPLETA.md (30 páginas)
- **Ejecutivo:** backend/RESUMEN_EJECUTIVO.md
- **PWA:** frontend/pwa-setup/GUIA_INSTALACION_PWA.md

### APIs Externas
- **Claude AI:** Anthropic API (Sonnet 4)
- **Tasas cambio:** frankfurter.app (gratis)
- **Emails:** Brevo API
- **Storage:** Cloudinary

### Soporte
- **Developer:** Julio (lilpapaja)
- **Cliente:** Dazz Creative
- **Usuarios:** Miguel, Julieta, Antonio

---

## 🎯 Objetivos Claude Code

1. **Optimizar:** Refactorizar Statistics.jsx, queries N+1, bundle size
2. **Testing:** 70%+ coverage backend, E2E críticos frontend
3. **Quality:** Code review, best practices, documentación actualizada
4. **Features:** Push notifications, analytics dashboard, búsqueda avanzada

---

**Última actualización:** 2026-03-11  
**Estado:** Producción activa - Optimización continua

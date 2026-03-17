# Memory - Contexto del Proyecto

## 🎯 Proyecto

**Nombre:** Dazz Producciones  
**Descripción:** Sistema gestión gastos con IA para productora audiovisual  
**Cliente:** Dazz Creative (productora Madrid)  
**Estado:** ✅ Producción activa (módulo proveedores completado 6 fases)
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
- **Storage:** Cloudinary (dazz-producciones/tickets/ + dazz-suppliers/invoices/)
- **Storage certificados:** Cloudflare R2 (certificados bancarios proveedores)
- **Deploy:** Railway (auto-deploy desde GitHub)
- **Variable Railway:** SUPPLIER_PORTAL_URL configurada

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
- **Frontend DAZZ:** https://dazz-producciones.vercel.app
- **Portal Proveedores:** https://dazzsuppliers.vercel.app

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
│   │   ├── companies.py     # Multi-tenant
│   │   └── suppliers.py     # 23 endpoints proveedores
│   └── services/
│       ├── claude_ai.py              # Extracción IA (tickets + facturas proveedores)
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
11. **Módulo Proveedores** - ✅ Completado 6 fases (ver sección dedicada abajo)

### ⏸️ Pendientes (Roadmap)
- Testing completo módulo proveedores + correcciones menores
- Tests unitarios backend (0% coverage)
- Tests E2E frontend (Playwright)
- Push notifications PWA
- Dashboard analytics

---

## 🏭 Módulo Proveedores (Completado 2026-03-16)

### 6 Fases de implementación
1. **BD + Modelos** - Tablas suppliers, supplier_invoices, bank_certificates en PostgreSQL
2. **IA Extracción** - Claude extrae datos de facturas de proveedores automáticamente
3. **Backend completo** - 23 endpoints en `routes/suppliers.py`
4. **UI Admin DAZZ** - Gestión proveedores integrada en frontend principal (dazz-producciones.vercel.app)
5. **Portal del Proveedor** - App independiente en `frontend-suppliers/` desplegada en dazzsuppliers.vercel.app
6. **Integración completa** - Backend ↔ Portal ↔ Admin UI conectados

### Infraestructura
- **Portal proveedores:** frontend-suppliers/ → Vercel (dazzsuppliers.vercel.app)
- **Tema portal:** zinc/amber (mismo que DAZZ principal)
- **Variable Railway:** `SUPPLIER_PORTAL_URL` configurada para enlaces en emails
- **Cloudflare R2:** Certificados bancarios de proveedores
- **Cloudinary separado:**
  - `dazz-producciones/tickets/` → Tickets internos DAZZ
  - `dazz-suppliers/invoices/` → Facturas de proveedores

### Auditoría
- 20+ fixes aplicados durante auditoría pre-testing
- Testing automatizado 2026-03-16: 25 issues encontrados (3 critical, 7 high, 8 medium, 7 low)

### Testing completado (2026-03-16)
- ✅ 22/22 endpoints routing OK (ningún 500)
- ✅ 21/21 endpoints protegidos devuelven 401 sin auth
- ✅ CORS correcto (DAZZ + portal permitidos, orígenes externos bloqueados)
- ✅ 6/6 security headers presentes
- ✅ Validaciones login/registro funcionan (email, password strength, GDPR)
- ✅ Token validation devuelve `{valid: false}` para tokens fake
- ✅ Refresh/logout manejan tokens inválidos correctamente
- ✅ Endpoints existentes (auth, projects, tickets, stats) sin regresión
- ❌ `/health` y `/` devuelven 500 (bug rate limiter slowapi)
- ⚠️ Rate limiting no se activa (workers gunicorn no comparten memoria)

### Estado actual (2026-03-17)
- ✅ 3 CRITICAL arreglados: C-1 IBAN encriptado Fernet, C-2 file stream fix, C-3 rate limiting
- ✅ 7 HIGH arreglados: H-1/H-2 N+1 joinedload, H-3 date String→Date migración, H-4 magic bytes PDF, H-5 filename sanitize, H-6 logout auth, H-7 enum Literal
- ✅ Bug OC validation: lógica INFLUENCER/GENERAL/MIXED implementada
- ✅ UI Admin proveedores en español (mockup v4): 7 páginas traducidas
- ✅ SupplierDetail completado: buscador ProjectView, modal editar, export Excel, notas con ✕, acciones factura, lightbox PDF
- ✅ InvoiceDetail nuevo: detalle factura con datos, importes, validación IA, acciones, navegación anterior/siguiente
- ✅ InvoicesList completado: sin columna IA, Trash2 funcional con modal motivo, buscador con voz
- ✅ Grupo 1 UI fixes: bank cert View PDF, custom message invitación, cert upload error visible
- ⏳ UI admin pendiente: SuppliersDashboard revisar, SupplierNotifications revisar
- ⏳ Portal proveedor: pendiente revisión UI completa
- ✅ Cloudinary fixes (2026-03-17): DELETE factura borra PDF+páginas, páginas usan folder correcto `dazz-suppliers/pages/{supplier_id}/`, `delete_invoice_pdf` extrae public_id de URL antes de destroy

---

## 🚨 Issues Módulo Proveedores (25 encontrados 2026-03-16)

### CRITICAL (3) — ✅ TODOS ARREGLADOS (2026-03-17)
1. ~~**C-1: IBAN sin encriptar**~~ → Fernet encryption + migrate-ibans endpoint
2. ~~**C-2: File stream consumido**~~ → contents bytes directos, sin seek
3. ~~**C-3: Sin rate limiting registro**~~ → 10/min validate, 5/hour register

### HIGH (7) — ✅ TODOS ARREGLADOS (2026-03-17)
4. ~~**H-1: N+1 list_suppliers**~~ → joinedload + batch aggregation (351→4 queries)
5. ~~**H-2: N+1 list_invoices**~~ → joinedload(supplier) (51→1 query)
6. ~~**H-3: date String→Date**~~ → date_parsed columna via ALTER TABLE + parse_invoice_date 11 formatos
7. ~~**H-4: Content-type spoofing**~~ → validate_pdf_bytes magic bytes %PDF
8. ~~**H-5: Filename no sanitizado**~~ → sanitize_filename de validators.py
9. ~~**H-6: Logout sin auth**~~ → Depends(get_current_active_supplier) + supplier_id ownership
10. ~~**H-7: Status sin validar enum**~~ → Literal["APPROVED","PAID","REJECTED"]

### MEDIUM (8)
11. Índice compuesto faltante (supplier_id, status) en invoices
12. Índice compuesto faltante (recipient_type, recipient_id, is_read) en notifications
13. Full table scan SupplierOC para NIF matching en registro
14. supplier_type acepta string arbitrario (falta enum validation)
15. OC_PENDING invoices sin path de borrado
16. Notificaciones commit separado del invoice (gap atomicidad)
17. DELETE_REQUESTED no en transition table (error confuso)
18. File copy síncrono en endpoint async (bloquea event loop)

### LOW (7)
19. onupdate lambda no se ejecuta en bulk updates
20. Double logout devuelve 400 (debería ser 200 idempotente)
21. Dead code: validación password duplicada en schema
22. TODO misleading sugiere encriptación que no existe
23. IBAN masking no valida formato antes de enmascarar
24. Math tolerance fija (2 céntimos) falla en facturas grandes
25. Admin notifications hardcodean recipient_id=0

### Otros problemas conocidos
- **Sin tests automatizados:** 0% coverage backend y frontend
- **Bug rate limiter:** `/` y `/health` devuelven 500 por slowapi

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
- **Claude AI:** Anthropic API (Sonnet 4) - tickets + facturas proveedores
- **Tasas cambio:** frankfurter.app (gratis)
- **Emails:** Brevo API
- **Storage tickets:** Cloudinary (dazz-producciones/tickets/)
- **Storage facturas proveedores:** Cloudinary (dazz-suppliers/invoices/)
- **Storage certificados bancarios:** Cloudflare R2

### Soporte
- **Developer:** Julio (lilpapaja)
- **Cliente:** Dazz Creative
- **Usuarios:** Miguel, Julieta, Antonio

---

## 🎯 Objetivos Claude Code

1. ~~**Fixes CRITICAL proveedores:**~~ ✅ C-1, C-2, C-3 arreglados
2. ~~**Fixes HIGH proveedores:**~~ ✅ H-1 a H-7 arreglados
3. **UI Admin proveedores:** En progreso — SupplierDetail, InvoicesList, InvoiceDetail completados. Pendiente: SuppliersDashboard, SupplierNotifications revisar
4. **Portal proveedor UI:** Pendiente revisión completa
5. **Fixes MEDIUM proveedores:** 8 pendientes (índices, atomicidad, etc.)
6. **Testing general:** 70%+ coverage backend, E2E críticos frontend
7. **Quality:** Code review, best practices, documentación actualizada
8. **Features:** Push notifications, analytics dashboard, búsqueda avanzada

---

**Última actualización:** 2026-03-17
**Estado:** Producción activa — CRITICAL+HIGH arreglados, Cloudinary fixes completados, UI admin en progreso, portal proveedor pendiente

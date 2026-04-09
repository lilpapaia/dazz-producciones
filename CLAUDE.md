# CLAUDE.md - Dazz Producciones v3.0

> **Centro de Control del Proyecto** - Sistema gestión gastos con IA  
> **Estado:** ✅ Producción activa - Railway + Vercel  
> **Última actualización:** 2026-04-10

---

## 📋 INICIO RÁPIDO

### Antes de empezar CUALQUIER tarea:
1. Lee `.claude/tasks/todo.md` → Próxima tarea prioritaria
2. Lee `.claude/tasks/lessons.md` → Errores NO repetir
3. Lee `.claude/memory.md` → Contexto proyecto
4. Lee este CLAUDE.md → Arquitectura y reglas

### Workflow típico:
```
1. Plan mode: Analizar + proponer solución → WAIT APPROVAL
2. Implementation: Ejecutar solo después de aprobación
3. Verification: Probar que funciona
4. Documentation: Actualizar .claude/tasks/lessons.md si aprendiste algo
5. Update TODO: Marcar tarea completa en .claude/tasks/todo.md
```

---

## 🎯 PROYECTO

**Nombre:** Dazz Producciones  
**Stack:** FastAPI + React + Claude AI + PostgreSQL  
**Deploy:** Railway (backend) + Vercel (frontend)  
**URLs:**
- Backend: https://dazz-producciones-production.up.railway.app
- Frontend: https://dazz-producciones.vercel.app

---

## 🏗️ ARQUITECTURA

### Base de Datos (PostgreSQL producción / SQLite local)

```sql
-- Tablas principales
users              # Usuarios (ADMIN/BOSS/WORKER)
companies          # Empresas (multi-tenant)
user_companies     # Many-to-many usuarios ↔ empresas
projects           # Proyectos (owner_company_id)
tickets            # Facturas/tickets (is_foreign, currency, country_code)
password_reset_tokens  # Reset contraseña
```

**Relaciones clave:**
- `User` ←→ `Company` (many-to-many vía user_companies)
- `Project` → `Company` (FK owner_company_id)
- `Project` → `User` (FK owner_id)
- `Ticket` → `Project` (FK project_id)

### Backend (FastAPI)

```
backend/
├── app/
│   ├── models/
│   │   ├── database.py       # SQLAlchemy models
│   │   └── schemas.py        # Pydantic schemas
│   ├── routes/               # Endpoints API
│   │   ├── auth.py          # Login, register, JWT
│   │   ├── projects.py      # CRUD + cierre proyectos
│   │   ├── tickets.py       # Upload + IA extracción
│   │   ├── statistics.py    # Stats + IVA extranjero
│   │   ├── users.py         # CRUD usuarios
│   │   └── companies.py     # Gestión empresas
│   └── services/             # Lógica negocio
│       ├── claude_ai.py              # Extracción IA tickets
│       ├── email.py                  # Brevo API emails
│       ├── excel_generator.py        # Excel BytesIO
│       ├── exchange_rate.py          # Tasas históricas
│       ├── geographic_classifier.py  # NACIONAL/UE/INT
│       └── companies_service.py      # Permisos multi-tenant
├── config/
│   └── database.py          # Auto-detect SQLite/PostgreSQL
├── main.py                  # FastAPI app
└── requirements.txt
```

**21 Endpoints principales:**
- Auth: `/auth/login`, `/auth/register`, `/auth/set-password`
- Projects: `/projects` (GET/POST/PUT/DELETE), `/projects/{id}/close`
- Tickets: `/tickets/{project_id}/upload`, `/tickets/{id}` (GET/PUT/DELETE)
- Statistics: `/statistics/complete` (año, trimestre, empresa, geo)
- Users: `/users` (CRUD, permisos admin)
- Companies: `/companies` (GET filtrado por rol)

### Frontend (React)

```
frontend/
├── src/
│   ├── pages/                # Páginas principales
│   │   ├── Login.jsx
│   │   ├── Dashboard.jsx
│   │   ├── ProjectCreate.jsx, ProjectView.jsx
│   │   ├── UploadTickets.jsx      # Camera + compresión
│   │   ├── ReviewTicket.jsx       # Corrección + lightbox
│   │   ├── ProjectCloseReview.jsx # Preview + selector emails
│   │   ├── Statistics.jsx         # ⚠️ 500+ líneas (REFACTOR)
│   │   └── Users.jsx
│   ├── components/
│   │   ├── Navbar.jsx             # Logo SVG Dazz
│   │   ├── EmailChipsInput.jsx    # Selector emails chips
│   │   └── PWAComponents.jsx      # Update/install prompts
│   ├── context/
│   │   └── AuthContext.jsx        # Auth global
│   ├── services/
│   │   └── api.js                 # Axios interceptors
│   └── App.jsx                    # Routing + protected routes
├── public/
│   ├── icons/                     # PWA iconos 8 tamaños
│   └── favicon.svg
└── vite.config.js                 # PWA + code splitting
```

**7 Páginas React:**
1. Login (auth)
2. Dashboard (overview proyectos)
3. ProjectCreate / ProjectView (CRUD)
4. UploadTickets (camera + IA)
5. ReviewTicket (corrección)
6. ProjectCloseReview (preview + emails)
7. Statistics (gráficos + IVA)
8. Users (gestión usuarios, admin only)

---

## 💡 DECISIONES ARQUITECTÓNICAS CRÍTICAS

### 1. IA Claude Sonnet 4 - Extracción Automática
```python
# backend/app/services/claude_ai.py
def extract_ticket_data(file_path: str, mime_type: str) -> dict:
    """
    Extrae datos de ticket con Claude:
    - Proveedor, fecha, importes, IVA
    - Moneda extranjera (USD, GBP, CHF...)
    - País (código ISO: US, GB, ES...)
    - Clasificación geo: NACIONAL, UE, INTERNACIONAL
    """
```
**Por qué Claude:** Facturas muy variadas (formatos, idiomas, layouts)  
**Resultado:** ~95% precisión, detecta moneda/país automático

### 2. Brevo API - Emails (NO SMTP)
```python
# backend/app/services/email.py
# Railway bloquea SMTP (puerto 587) → Usar API REST
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"
```
**Por qué REST:** Railway bloquea puertos SMTP  
**Resultado:** Emails funcionan perfecto

### 3. BytesIO - Excel en Memoria (NO Filesystem)
```python
# backend/app/services/excel_generator.py
excel_bytes = BytesIO()
workbook.save(excel_bytes)
excel_bytes.seek(0)
return excel_bytes.getvalue()
```
**Por qué memoria:** Railway no persistente, más rápido  
**Resultado:** Compatible cloud, sin basura disco

### 4. Multi-tenant - Tabla Companies
```sql
CREATE TABLE companies (id, name, cif, ...);
CREATE TABLE user_companies (user_id, company_id);  -- Many-to-many
ALTER TABLE projects ADD COLUMN owner_company_id INTEGER FK companies;
```
**Por qué separado:** Dazz tiene 3+ empresas legales, permisos granulares  
**Resultado:** ADMIN ve todo, BOSS solo su empresa

### 5. PWA - Cámara Móvil Directa
```jsx
<input 
  type="file" 
  accept="image/*"
  capture="environment"  // Abre cámara trasera móvil
/>
```
**Por qué capture:** Escaneo facturas in-situ (restaurantes, tiendas)  
**Resultado:** App instalable, funciona offline

### 6. Compresión Automática - browser-image-compression
```javascript
// Fotos móvil 6-8MB → Claude API límite 5MB
if (file.size > 3 * 1024 * 1024) {
  compressedFile = await imageCompression(file, { maxSizeMB: 3 });
}
```
**Por qué automático:** Usuario no debe preocuparse  
**Resultado:** Fotos móvil funcionan sin error

### 7. Dark Theme - Zinc/Amber Branded
```css
/* Identidad visual Dazz Creative */
bg-zinc-950  /* Fondo casi negro */
text-zinc-100  /* Texto blanco */
text-amber-500  /* Accents dorados */
```
**Por qué:** Profesional, reduce fatiga, distintivo  
**Resultado:** Diseño coherente branded

### 8. PostgreSQL Auto-Switch
```python
# config/database.py (ÚNICO archivo de config BD — database_config.py NO debe existir)
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:  # Railway — incluye fix postgres:// → postgresql://
    engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10, pool_pre_ping=True)
else:  # Local
    engine = create_engine("sqlite:///./dazz_producciones.db")
```
**Por qué:** Desarrollo fácil (SQLite), producción robusta (PostgreSQL)  
**Resultado:** Mismo código dos entornos. Un solo engine/pool compartido

---

## 🚨 REGLAS CRÍTICAS - NUNCA VIOLAR

### ❌ NUNCA hacer:
1. **Subir .env a GitHub** - Contiene secretos (API keys, DATABASE_URL)
2. **Usar SMTP en Railway** - Puerto 587 bloqueado, usar Brevo API
3. **Guardar Excel en disco** - Railway no persistente, usar BytesIO
4. **Usar URLs internas Railway en local** - `postgres.railway.internal` NO funciona
5. **Hacer cambios directo GitHub web + local** - Conflictos Git
6. **Quotes largas de search results** - Copyright: máximo 15 palabras
7. **Cambiar estructura BD sin migración** - Rompe producción
8. **Guardar IBANs en plaintext** - Siempre Fernet encryption o no guardar
9. **Usar window.confirm()** - Siempre ConfirmDialog custom (dark theme)
10. **Borrar código sin grep -r** - Un import roto tumba producción
11. **Silenciar errores API con catch vacío** - Mostrar error al usuario
12. **Polling global sin condición de ruta** - Solo en la página que lo necesita
13. **Duplicar funciones entre auth.py y supplier_auth.py** - Importar siempre de auth.py
14. **Hardcodear años** (ej: `default="2026"`) - Usar `datetime.now().year`
15. **Usar `application/octet-stream`** como MIME permitido - Demasiado permisivo
16. **Mezclar importes monetarios con conteos** en el mismo gráfico

### ✅ SIEMPRE hacer:
1. **Plan-first:** Analizar → Proponer → WAIT APPROVAL → Ejecutar
2. **Verificar antes de completo:** Test que funciona antes marcar done
3. **Actualizar lessons.md:** Si encontraste bug, documenta cómo prevenir
4. **Usar joinedload:** Evitar N+1 queries (projects + tickets + owner_company)
5. **Validar backend:** Pydantic schemas + permisos por rol
6. **Responsive design:** Mobile-first (mayoría usuarios móvil)
7. **Git workflow:** Pull → Code → Commit → Push
8. **case() floor a 0** en decrementos de tickets_count y total_amount (3 sitios)
9. **previous_status** antes de cambiar a DELETE_REQUESTED (2 sitios: tickets.py, supplier_portal.py)
10. **Refresh interceptor con guard URLs** login/refresh en AMBOS frontends
11. **Magic bytes validation** en uploads (JPEG, PNG, PDF, WebP, HEIC)
12. **Feedback UX obligatorio:** loading + error + success en TODA acción
13. **Botones async con disabled + loading** para evitar doble-tap
14. **useMemo** para context Provider values y valores computados costosos
15. **useCallback** para funciones en contextos y pasadas como props
16. **Unique constraints** en campos de negocio (creative_code, invoice_number)
17. **Verificar 6 sitios de borrado** si cambias estados permitidos (InvoicesList, InvoiceDetail, SupplierDetail, Home portal, supplier_portal.py, suppliers.py)

---

## 📐 ESTÁNDARES DE CÓDIGO

### Backend (Python)
```python
# Type hints siempre
def create_project(project: schemas.ProjectCreate, db: Session) -> Project:
    pass

# Error handling con HTTPException
if not user:
    raise HTTPException(status_code=404, detail="User not found")

# Pydantic v2: .model_dump() NO .dict()
update_data = ticket_update.model_dump(exclude_unset=True)
db_project = Project(**project.model_dump(exclude={"company"}), ...)

# lifespan context manager (NO @app.on_event("startup"))
@asynccontextmanager
async def lifespan(app):
    # migrations here
    yield
app = FastAPI(lifespan=lifespan)

# SQLAlchemy: from sqlalchemy.orm import declarative_base (NO sqlalchemy.ext.declarative)

# Docstrings funciones complejas
def extract_ticket_data(file_path: str) -> dict:
    """Extrae datos de ticket con Claude AI."""
```

### Frontend (React)
```jsx
// Functional components + hooks
const Statistics = () => {
  const [data, setData] = useState(null);
  
  useEffect(() => {
    loadData();
  }, []);
  
  return <div>...</div>;
};

// Tailwind inline, no CSS separado
<button className="bg-amber-500 hover:bg-amber-600 px-6 py-3 rounded-sm">
  CREAR PROYECTO
</button>

// Props con destructuring
const EmailChip = ({ email, onRemove }) => (
  <span>{email} <X onClick={onRemove} /></span>
);
```

### Commits
```bash
# Conventional Commits
feat(backend): añadir endpoint estadísticas IVA extranjero
fix(frontend): corregir compresión imágenes >5MB
refactor(statistics): dividir Statistics.jsx en componentes
docs: actualizar RESUMEN_EJECUTIVO con features completadas
```

---

## 🎨 DESIGN SYSTEM

### Colores
```javascript
// Zinc (grises oscuros)
'bg-zinc-950'    // Fondo principal
'bg-zinc-900'    // Cards, modales
'bg-zinc-800'    // Bordes activos
'text-zinc-100'  // Texto principal
'text-zinc-400'  // Texto secundario

// Amber (dorado - accent)
'text-amber-500'       // Primary
'bg-amber-500'         // Buttons
'hover:bg-amber-600'   // Button hover
'border-amber-500'     // Focus states

// Estados
'text-green-400'   // Success
'text-red-400'     // Error
'text-blue-400'    // Info
'text-purple-400'  // Internacional (geo)
```

### Tipografía
```css
/* Títulos */
font-family: 'Bebas Neue';
text-transform: uppercase;
letter-spacing: 0.1em;

/* Código */
font-family: 'IBM Plex Mono';

/* Cuerpo */
font-family: system-ui;
```

### Componentes
```jsx
// Buttons
<button className="bg-amber-500 hover:bg-amber-600 text-zinc-950 px-6 py-3 rounded-sm font-bold transition-all shadow-lg shadow-amber-500/30">

// Cards
<div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6">

// Inputs
<input className="bg-zinc-900 border border-zinc-700 text-zinc-100 px-4 py-2 rounded-sm focus:border-amber-500 focus:ring-1 focus:ring-amber-500">

// Badges
<span className="bg-amber-500/20 text-amber-400 px-2 py-1 rounded text-xs">
```

---

## 🔐 PERMISOS Y ROLES

### ADMIN
```python
# Ve TODO, hace TODO
if user.role == "ADMIN":
    projects = db.query(Project).all()  # Todos los proyectos
    companies = db.query(Company).all()  # Todas las empresas
```

### BOSS
```python
# Solo su empresa
if user.role == "BOSS":
    company_ids = [c.id for c in user.companies]
    projects = db.query(Project).filter(
        Project.owner_company_id.in_(company_ids)
    ).all()
```

### WORKER
```python
# Solo SUS proyectos de sus empresas
if user.role == "WORKER":
    company_ids = [c.id for c in user.companies]
    projects = db.query(Project).filter(
        Project.owner_id == user.id,
        Project.owner_company_id.in_(company_ids)
    ).all()
```

**Verificación acceso:**
```python
def can_access_project(user: User, project: Project) -> bool:
    if user.role == "ADMIN":
        return True
    if user.role == "BOSS":
        return project.owner_company_id in [c.id for c in user.companies]
    return project.owner_id == user.id
```

---

## 🧪 TESTING

### Backend (pytest) — 335 tests, 16 módulos
```bash
pytest --cov=app --cov-report=html

# Módulos: auth, projects, tickets, statistics, users, companies,
# permissions, roles, security, suppliers (admin + portal),
# autoinvoice, OCs, schemas, ticket_upload
```

### Frontend (Playwright) — Pendiente
```bash
# Setup pendiente
npx playwright test
```

---

## 📊 MÉTRICAS Y MONITOREO

### Performance Targets
- **Initial bundle:** <200KB (actual: ~332KB, 63% reducción desde 893KB) ✅
- **Statistics render:** <100ms (refactorizado en 13 módulos con memo) ✅
- **API response:** <200ms average ✅
- **Database queries:** GROUP BY + joinedload optimizados ✅

### Coverage
- **Backend tests:** 335 tests, 16 módulos ✅
- **Frontend E2E:** Pendiente (Playwright) 🔴

### Monitoreo Railway
- **Logs:** Railway dashboard → Deployments → Logs
- **Metrics:** CPU, RAM, requests/s
- **Database:** PostgreSQL queries lentas

---

## 🚀 DEPLOYMENT

### Backend (Railway)
```yaml
# railway.json
{
  "build": { "builder": "NIXPACKS" },
  "deploy": {
    "startCommand": "gunicorn main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT"
  }
}
```
**Auto-deploy:** Push a `main` → Railway detecta → Build → Deploy (~2 min)

### Frontend (Vercel)
```javascript
// vite.config.js
export default defineConfig({
  plugins: [react(), VitePWA({ ... })],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'chart-vendor': ['recharts'],
        }
      }
    }
  }
})
```
**Auto-deploy:** Push a `main` → Vercel detecta → Build → Deploy (~1 min)

---

## 🔧 TROUBLESHOOTING

### Error: "DATABASE_URL postgres.railway.internal"
```bash
# Local debe usar SQLite
DATABASE_URL=sqlite:///./dazz_producciones.db

# Railway usa PostgreSQL automático (variable entorno)
```

### Error: "Could not send email"
```bash
# Verificar Brevo API key en Railway
BREVO_API_KEY=xkeysib-...

# NO usar SMTP (bloqueado)
```

### Error: "File too large 413"
```bash
# Verificar compresión automática activa
# browser-image-compression debe comprimir >3MB
```

### Error: "Forbidden 403 project access"
```bash
# Verificar permisos:
# - WORKER solo ve SUS proyectos
# - BOSS solo ve su EMPRESA
# - ADMIN ve TODO
```

---

## 📝 PRÓXIMOS PASOS (Ver .claude/tasks/todo.md)

### ✅ Completado
- [x] Refactorizar Statistics.jsx (892 → 13 módulos)
- [x] Optimizar queries N+1 (joinedload + GROUP BY)
- [x] Code splitting frontend (893KB → 332KB)
- [x] Tests backend (335 tests, 16 módulos)
- [x] Auditoría exhaustiva v5 (91 hallazgos, 67 resueltos, 13 commits)

### Pendiente
- [ ] Tests E2E frontend (Playwright, flujos críticos)
- [ ] GitHub Actions CI/CD
- [ ] Push notifications PWA
- [ ] Alembic para migraciones (reemplazar ALTER TABLE en startup)

---

## 📞 CONTACTO

**Developer:** Julio (lilpapaja) - GitHub: https://github.com/lilpapaja/dazz-producciones  
**Cliente:** Dazz Creative - Madrid  
**Usuarios principales:** Miguel (ADMIN), Julieta (BOSS), Antonio (BOSS)

---

**Última actualización:** 2026-04-10  
**Versión:** v3.0  
**Estado:** ✅ Producción activa - Optimización continua

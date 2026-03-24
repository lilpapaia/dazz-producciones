# Lessons Learned - Self-Improvement

## 📋 Formato

```
## YYYY-MM-DD: [Categoría] - [Título del error]
**Error:** [Qué salió mal específicamente]
**Causa raíz:** [Por qué pasó]
**Solución:** [Cómo se arregló]
**Regla:** [Regla preventiva para el futuro]
**Prevención:** [Checklist antes de ejecutar]
```

---

## 2026-03-11: [Setup] - Estructura .claude/ creada

**Contexto:** Instalación Claude Code y setup inicial del proyecto
**Decisión:** Usar estructura .claude/ para persistir contexto entre sesiones
**Beneficio:** Claude recuerda TODO automáticamente sin re-explicar
**Aplicación:** Template reutilizable para futuros proyectos

---

## 2026-03-11: [Configuración] - DATABASE_URL local vs producción

**Error:** Usar URL interna de Railway (`postgres.railway.internal`) en desarrollo local causaba errores de conexión
**Causa raíz:** Copiar variables de Railway sin adaptar para local
**Solución:** 
- Local: `DATABASE_URL=sqlite:///./dazz_producciones.db`
- Producción: Railway usa PostgreSQL automático
**Regla:** NUNCA usar URLs internas de Railway en local
**Prevención:** 
- Verificar .env antes de arrancar servidor
- database_config.py auto-detecta entorno

---

## 2026-03-11: [Git] - Conflictos por trabajar directo en GitHub web

**Error:** Hacer cambios en GitHub web + cambios locales sin pull = conflictos
**Causa raíz:** No usar workflow Git correcto (pull antes de push)
**Solución:** Clonar repo limpio, workflow ordenado
**Regla:** SIEMPRE pull antes de empezar a trabajar
**Prevención:**
- Pull → Código → Commit → Push
- No editar directo en GitHub web si trabajas local

---

## 2026-03-11: [Documentación] - RESUMEN_EJECUTIVO.md desactualizado

**Error:** Docs dicen "Próximamente: Estadísticas, Moneda extranjera" pero ya están implementados
**Causa raíz:** No actualizar docs después de cada feature
**Solución:** Revisar y actualizar RESUMEN_EJECUTIVO.md
**Regla:** Actualizar docs al terminar cada sprint
**Prevención:** 
- Checklist fin de tarea: "¿Docs actualizados?"
- README.md siempre refleja estado actual

---

## 2026-03-11: [Performance] - Optimización Queries N+1 en Statistics

**Error:** Endpoints /statistics/complete hacían 50+ queries por request (queries en loops)
**Causa raíz:** 
- statistics.py hacía `db.query()` dentro de loops (por país, por empresa)
- projects.py y users.py sin joinedload en relaciones
- Validaciones en loops (1 query por item)

**Solución implementada:**
- **Pre-fetch batch:** Cargar todos los projects/companies ANTES del loop en 1 query
- **joinedload():** Cargar relaciones eagerly (Project.owner_company, User.companies)
- **func.count():** COUNT directo en BD vs traer objetos a Python
- **Validación batch:** 1 query para múltiples IDs

**Archivos modificados:**
- backend/app/routes/statistics.py (3 optimizaciones críticas)
- backend/app/routes/projects.py (joinedload)
- backend/app/routes/users.py (joinedload + validación batch)

**Resultado:**
- /statistics/complete: ~50 queries → ~5-7 queries (85% reducción)
- Tiempo respuesta mejorado significativamente
- Funcionalidad 100% intacta (verificado en local)

**Regla:** SIEMPRE usar joinedload() para relaciones que se acceden en serialización
**Regla:** NUNCA hacer queries dentro de loops - pre-fetch en batch
**Regla:** Usar func.count() cuando solo necesitas contar, no los objetos completos

**Prevención:**
- Checklist antes de merge: ¿Hay queries en loops?
- Activar SQL logging en desarrollo para detectar N+1
- Code review enfocado en queries
- Pattern: Primero cargar IDs únicos → luego batch query con .in_(ids)

---

## 2026-03-11: [Performance] - Code Splitting Frontend con React.lazy

**Error:** Bundle inicial 893 KB - todas las páginas y librerías cargaban al entrar (Login)
**Causa raíz:**
- Imports estáticos de todas las rutas en App.jsx
- jsPDF (385 KB) + html2canvas (201 KB) en bundle principal
- Recharts (366 KB) cargaba aunque solo se usa en Statistics
- Usuario descargaba TODO antes de poder usar Login

**Solución implementada:**
- **React.lazy():** 8 rutas convertidas a lazy load (Statistics, Users, ProjectCreate, etc.)
- **Suspense:** Fallback spinner branded (zinc/amber) mientras cargan páginas
- **Dynamic import jsPDF:** Solo carga cuando usuario exporta PDF
- **Eager load:** Login y Dashboard (páginas críticas) siguen cargando al inicio

**Archivos modificados:**
- frontend/src/App.jsx (lazy imports + Suspense wrapper)
- frontend/src/pages/Statistics.jsx (dynamic import jsPDF)
- frontend/vite.config.js (limpieza manualChunks)

**Resultado:**
- Bundle inicial: 893 KB → 332 KB (63% reducción)
- Bundle JS inicial: 816 KB → 255 KB (69% reducción)
- Gzip inicial: 254 KB → 82 KB (68% reducción)
- jsPDF + html2canvas: 586 KB on-demand (solo al exportar)
- Recharts: 366 KB on-demand (solo en Statistics)
- Carga inicial 3x más rápida
- Funcionalidad 100% intacta (verificado en local)

**Regla:** SIEMPRE lazy load páginas secundarias (no críticas)
**Regla:** Mantener eager solo Login + página principal (Dashboard)
**Regla:** Dynamic import librerías pesadas que se usan ocasionalmente
**Regla:** Añadir Suspense con fallback branded para UX consistente

**Prevención:**
- Build regular con `npm run build` para monitorear tamaños
- Revisar chunks grandes (>100KB) y evaluar lazy load
- Pattern: Páginas secundarias → lazy(), librerías ocasionales → dynamic import
- Verificar que PWA cachea todos los chunks tras primera visita

---

## 2026-03-11: [Frontend] - Refactor Statistics.jsx de monolito a módulos

**Error:** Statistics.jsx con 892 líneas - difícil mantener, render lento (~300ms), componentes inline
**Causa raíz:**
- Todo en un solo archivo: estado, lógica, componentes, servicios
- PDF export inline (169 líneas)
- 4 cards copy-paste del mismo código
- Componentes internos (TicketRow, ProjectRow) se re-creaban en cada render
- Sin React.memo ni useMemo - re-renderiza TODO al cambiar filtros

**Solución implementada:**
- **Estructura modular:** 1 archivo → 13 archivos especializados
- **Hooks custom:** useStatisticsData (fetch + estado), useExpandedState (toggle)
- **Servicios:** pdfExport.js extraído (175 líneas independientes)
- **Componentes reutilizables:** StatCard (elimina 4 copy-paste)
- **React.memo:** 7 componentes memoizados (evitan re-renders innecesarios)
- **useMemo:** Cálculos pesados (claimableBreakdown, legendFormatter)
- **useCallback:** Funciones estables (toggles, navigation, export)

**Estructura creada:**
```
Statistics/
├── index.jsx (144 líneas - orquestador)
├── hooks/ (useStatisticsData, useExpandedState)
├── services/ (pdfExport.js)
└── components/ (10 componentes 20-150 líneas c/u)
```

**Archivos modificados:**
- frontend/src/pages/Statistics.jsx → Statistics/index.jsx
- +12 archivos nuevos creados
- Statistics.jsx.old guardado como backup

**Resultado:**
- Archivo más grande: 175 líneas (vs 892 antes)
- Render time: <100ms (vs ~300ms) - 3x más rápido
- Re-renders: Solo componentes afectados (vs TODO)
- Bundle size: +1.3 KB overhead (despreciable)
- Mantenibilidad: 10x más fácil localizar y cambiar código
- Reutilización: StatCard, TicketRow, ProjectRow usables en otras páginas
- Funcionalidad 100% intacta (verificado en local)

**Regla:** Archivos >200 líneas considerar refactor a módulos
**Regla:** Componentes inline (dentro de render) → componentes separados con memo
**Regla:** Código duplicado (copy-paste) → componente reutilizable
**Regla:** Cálculos pesados sin deps cambiantes → useMemo
**Regla:** Funciones pasadas como props → useCallback para memo efectivo

**Prevención:**
- Límite sugerido: 150-200 líneas por archivo
- Si archivo crece >300 líneas → planificar refactor
- Checklist: ¿Hay código duplicado? ¿Componentes inline? ¿Cálculos sin memo?
- Pattern: hooks/ para lógica, services/ para utils, components/ para UI
- Verificar React DevTools Profiler: re-renders innecesarios indican falta de memo

---

## 2026-03-11: [Backend] - Código duplicado y validaciones faltantes

**Error:** Funciones de permisos duplicadas en múltiples archivos, validaciones Pydantic ausentes
**Causa raíz:**
- can_access_project() duplicada en projects.py y tickets.py (versiones ligeramente diferentes)
- _get_user_company_ids() duplicada en projects.py y companies_service.py
- auth.py validaba empresas en loop (N queries)
- schemas.py sin Field() validators (aceptaba negativos, passwords cortos, IVA >100%)
- cloudinary_service.py con bare except: (esconde errores críticos)

**Solución implementada:**
- **Centralización permisos:** Creado services/permissions.py con 3 funciones únicas
- **Eliminación duplicados:** Removidas funciones locales de projects.py (-46 líneas) y tickets.py (-17 líneas)
- **Batch query auth:** Validación empresas N queries → 1 query batch
- **Validaciones Pydantic:** Field(ge=0) para amounts, Field(0-100) para porcentajes, Field(min_length=6) para passwords
- **Error handling:** bare except: → except Exception: (no esconde errores críticos)
- **Seguridad mejorada:** tickets.py ahora verifica owner_company_id para WORKER (antes solo owner_id)

**Archivos modificados:**
- backend/app/services/permissions.py (creado - 62 líneas)
- backend/app/routes/projects.py (refactor imports - eliminó helpers)
- backend/app/routes/tickets.py (refactor imports - eliminó can_access_project)
- backend/app/routes/auth.py (batch query empresas)
- backend/app/models/schemas.py (Field validators añadidos)
- backend/app/services/cloudinary_service.py (fixed bare except)

**Resultado:**
- Código duplicado: 2 copias → 1 fuente única
- Funciones permisos: centralizadas en un solo archivo
- Validaciones: amounts ≥0, IVA 0-100%, passwords ≥6 chars
- Error handling: mejorado (no esconde errores críticos)
- Seguridad WORKER: mejorada (verifica empresa + owner)
- Mantenibilidad: cambiar permisos = 1 archivo vs 2+
- Funcionalidad 100% intacta (verificado en local)

**Regla:** NUNCA duplicar lógica de permisos - centralizar en services/
**Regla:** SIEMPRE validar inputs con Field() en schemas (defense in depth)
**Regla:** NUNCA bare except: - usar except Exception: mínimo
**Regla:** Batch queries para validaciones múltiples (evitar N+1)

**Prevención:**
- Code review: buscar funciones con nombres similares en archivos diferentes
- Checklist validaciones: ¿Amounts pueden ser negativos? ¿Strings vacíos? ¿Rangos sin límite?
- Pattern: Permisos → services/permissions.py, nunca en routes/
- Linter: configurar flake8/ruff para detectar bare except:
- Testing: intentar enviar datos inválidos (negativo, vacío, fuera de rango)

---

## 2026-03-17: [Storage] - Cloudinary destroy() necesita public_id, no URL

**Error:** `delete_invoice_pdf` recibía la URL completa de Cloudinary y la pasaba a `cloudinary.uploader.destroy()`, que fallaba silenciosamente sin borrar nada
**Causa raíz:** `destroy()` espera un `public_id` (e.g. `dazz-suppliers/invoices/123/factura`), no una URL (e.g. `https://res.cloudinary.com/.../dazz-suppliers/invoices/123/factura.pdf`)
**Solución:** Crear helper `extract_public_id_from_url(url)` que parsea la URL y extrae el public_id sin extensión, usarlo antes de llamar a `destroy()`
**Regla:** SIEMPRE usar `extract_public_id_from_url()` antes de `cloudinary.uploader.destroy()` cuando el dato almacenado es una URL
**Prevención:**
- Verificar qué formato se almacena en BD (URL vs public_id)
- Testear destroy() comprobando que el recurso ya no existe después

---

## 2026-03-17: [Storage] - Cloudinary: PDFs requieren config de seguridad

**Error:** PDFs subidos a Cloudinary devolvían error 404 o acceso denegado al intentar acceder por URL
**Causa raíz:** Por defecto Cloudinary bloquea delivery de PDFs y ZIPs por seguridad
**Solución:** En Cloudinary Dashboard → Settings → Security → marcar **"PDF and ZIP files delivery"** habilitado
**Regla:** Al configurar Cloudinary para un proyecto que sube PDFs, SIEMPRE verificar que "PDF and ZIP files delivery" esté habilitado en Settings → Security
**Prevención:**
- Checklist setup Cloudinary: ¿Se suben PDFs? → Habilitar delivery
- Si PDFs devuelven 404/403 en Cloudinary, verificar esta config primero

---

## 2026-03-17: [Storage] - Cloudinary upload_image() no acepta folder explícito

**Error:** Páginas de PDF se subían a la raíz de Cloudinary en vez del folder `dazz-suppliers/pages/{supplier_id}/`
**Causa raíz:** La función wrapper `upload_image()` del servicio no pasaba el parámetro `folder` a Cloudinary, o lo concatenaba mal con `public_id`
**Solución:** Usar `cloudinary.uploader.upload()` directamente con parámetro `folder` separado del `public_id` — Cloudinary combina ambos internamente
**Regla:** Para control total del path en Cloudinary, usar `cloudinary.uploader.upload(file, folder="path/to/folder", public_id="filename")` directamente, no wrappers que puedan omitir parámetros
**Prevención:**
- Verificar en Cloudinary Media Library que los archivos aparecen en el folder correcto después de upload
- Si un archivo aparece en la raíz, revisar si el folder se está pasando correctamente

---

## 2026-03-18: [Storage] - Cloudinary raw resources incluyen extensión en public_id

**Error:** `delete_invoice_pdf` extraía el public_id sin extensión (e.g. `dazz-suppliers/invoices/1/archivo`) pero `destroy()` no encontraba el recurso
**Causa raíz:** Para `resource_type="raw"`, Cloudinary incluye la extensión del archivo como parte del public_id (a diferencia de images donde se omite)
**Solución:** Añadir `.pdf` al public_id si no la tiene antes de llamar a `destroy()`
**Regla:** Para raw resources en Cloudinary, el public_id INCLUYE la extensión del archivo
**Prevención:**
- Al borrar raw resources, verificar que el public_id incluye la extensión
- Distinguir entre image (sin extensión) y raw (con extensión) al construir public_ids

---

## 2026-03-18: [Storage] - extract_public_id_from_url: 'raw' vs 'upload' en URLs Cloudinary

**Error:** `extract_public_id_from_url` buscaba 'upload' o 'raw' en la URL. Para PDFs la URL es `/raw/upload/v1234/...` y encontraba 'raw' antes que 'upload', resultando en un public_id incorrecto que incluía la versión
**Causa raíz:** El loop `if part in ['upload', 'raw']` hacía match con 'raw' primero en URLs de tipo `/raw/upload/`
**Solución:** Cambiar a `if part == 'upload'` — buscar solo 'upload' que siempre precede al versionado
**Regla:** En URLs de Cloudinary, el segmento relevante para extraer public_id es siempre 'upload', nunca 'raw' (que es el resource_type)
**Prevención:**
- Estructura URL Cloudinary: `/{resource_type}/{type}/v{version}/{public_id}`
- 'raw' y 'image' son resource_types, 'upload' es el delivery type

---

## 2026-03-18: [Frontend] - Forzar descarga de archivos en vez de abrir en navegador

**Error:** `window.open(url, '_blank')` abre PDFs en el navegador en vez de descargarlos
**Causa raíz:** El navegador interpreta el Content-Type del PDF y lo renderiza en una pestaña
**Solución:** Usar `fetch()` + `blob()` + crear anchor temporal con atributo `download` y nombre descriptivo
**Regla:** Para forzar descarga de archivos, SIEMPRE usar fetch+blob+anchor con atributo download
**Prevención:**
- Pattern: `fetch(url) → blob → URL.createObjectURL → anchor.download = nombre → click → revokeObjectURL`
- No olvidar limpiar: `a.remove()` y `URL.revokeObjectURL()`

---

## 2026-03-24: [Security] - HTTPBearer devuelve 403, no 401, sin token

**Error:** El interceptor frontend solo capturaba 401. Sin token, HTTPBearer de FastAPI devolvía 403 → interceptor no lo capturaba → no hacía refresh → redirigía a login
**Causa raíz:** FastAPI `HTTPBearer()` devuelve 403 Forbidden cuando falta el header Authorization, no 401 Unauthorized
**Solución:** `HTTPBearer(auto_error=False)` + check manual `if credentials is None: raise 401`. Interceptor solo captura 401 — 403 de permisos se propagan normalmente
**Regla:** NUNCA interceptar 403 para refresh token — los 403 son errores de permisos reales (non-admin en endpoint admin)
**Prevención:** Si HTTPBearer devuelve un status inesperado, usar `auto_error=False` y manejar manualmente

---

## 2026-03-24: [Frontend] - useEffect con searchParams + replaceState causa re-ejecución

**Error:** SetPassword.jsx leía token con `searchParams.get('token')` en useEffect con `[searchParams]` como deps. `replaceState` limpiaba la URL → searchParams cambiaba → effect se re-ejecutaba → token era null
**Causa raíz:** `window.history.replaceState` modifica la URL → React Router detecta cambio → `useSearchParams()` se actualiza → useEffect se re-ejecuta con searchParams vacío
**Solución:** Leer token con `new URLSearchParams(window.location.search).get('token')` y usar `[]` como deps (una sola ejecución)
**Regla:** Para leer query params una sola vez y luego limpiar la URL, usar `window.location.search` directamente en vez del hook de React Router
**Prevención:** Si usas `replaceState` para limpiar URLs, nunca dependas de `searchParams` en el mismo effect

---

## 2026-03-24: [Frontend] - Validación password debe estar sincronizada frontend ↔ backend

**Error:** Frontend validaba min 6 chars sin complejidad. Backend exigía min 8 + mayúscula + número + símbolo. Password pasaba frontend → backend rechazaba con 422 → error `[object Object]`
**Causa raíz:** Requisitos de password cambiaron en el backend (auditoría SEC-C4) pero frontend no se actualizó
**Solución:** Frontend alineado con backend. Parse de errores Pydantic: `Array.isArray(detail) ? detail.map(d => d.msg).join(', ')`
**Regla:** SIEMPRE sincronizar validaciones de formularios entre frontend y backend. Si el backend cambia, el frontend DEBE actualizarse
**Prevención:** Checklist de cambios backend: ¿Hay validaciones Pydantic nuevas? → Actualizar frontend correspondiente

---

## 2026-03-24: [Frontend] - Campos opcionales deben excluirse del request body si vacíos

**Error:** Modal editar usuario enviaba `password: ''` al backend → Pydantic rechazaba con min_length=8. Además, browser autorrellena campo password con credenciales guardadas
**Causa raíz:** El payload incluía todos los campos del form state, incluyendo password vacío
**Solución:** `if (!payload.password?.trim()) delete payload.password` + `autoComplete="new-password"` en el input
**Regla:** Campos opcionales con validación deben eliminarse del body si están vacíos, no enviarse como string vacío
**Prevención:** Antes de enviar form data, filtrar campos vacíos que el backend valida con restricciones

---

## 2026-03-24: [Backend] - Query WORKER debe incluir responsible además de owner_id

**Error:** WORKER veía 0 proyectos aunque era responsable. La query filtraba solo por `owner_id` (quien creó el proyecto), no por `responsible` (quien trabaja en él)
**Causa raíz:** `responsible` es un string con el nombre del responsable, no un FK. La query y `can_access_project`/`can_modify_project` solo verificaban `owner_id`
**Solución:** `or_(owner_id == user.id, func.lower(responsible) == username.lower())` en la query del listado + misma lógica en permissions.py
**Regla:** SIEMPRE mantener consistency entre la query del listado y las funciones de permisos (can_access/can_modify). Si el listado muestra un recurso, el usuario debe poder abrirlo
**Prevención:** Al cambiar la lógica de filtrado de un listado, verificar TODAS las funciones de permisos que controlan acceso individual al mismo recurso

---

## 2026-03-24: [Frontend] - Selector de responsable debe filtrarse por empresa del proyecto

**Error:** El selector de responsable en crear/editar proyecto mostraba todos los usuarios del sistema, permitiendo asignar un WORKER de empresa X a un proyecto de empresa Y
**Causa raíz:** GET /users/usernames no tenía parámetro de filtrado por empresa. El frontend no pasaba company_id al cargar el selector
**Solución:** Añadir company_id opcional a GET /users/usernames + UserAutocomplete recibe prop companyId y recarga cuando cambia + ProjectCreate resetea responsable al cambiar empresa + backend valida que responsable pertenece a la empresa del proyecto
**Regla:** El selector de responsable SIEMPRE debe filtrarse por la empresa del proyecto seleccionada. Cambiar empresa = resetear responsable
**Prevención:** Checklist crear proyecto: ¿El selector de responsable está vinculado a la empresa seleccionada?

---

## Template para futuras lecciones

```
## YYYY-MM-DD: [Categoría] - [Título]
**Error:** 
**Causa raíz:** 
**Solución:** 
**Regla:** 
**Prevención:** 
```

**Categorías comunes:**
- [Backend] - Errores API, queries, validaciones
- [Frontend] - Componentes, hooks, estado
- [Deploy] - Railway, Vercel, CI/CD
- [Testing] - Tests fallidos, coverage
- [Performance] - Optimizaciones, queries N+1
- [Security] - Auth, permisos, vulnerabilidades
- [UX] - Usabilidad, accesibilidad
- [IA] - Extracción datos, prompts Claude
- [Git] - Commits, branches, conflictos
- [Setup] - Instalaciones, configuraciones

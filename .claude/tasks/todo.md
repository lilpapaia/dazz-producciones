# TODO - Dazz Producciones

> **Auditoría exhaustiva v1:** 2026-03-18 (44 de 50 resueltos)
> **Auditoría exhaustiva v2:** 2026-03-28 (7 agentes, 53 hallazgos nuevos → 41 resueltos)
> **Auditoría exhaustiva v3:** 2026-03-29 (4 agentes, post-OC/autofactura — 4 hallazgos → 4 resueltos)
> **Auditoría calidad v4:** 2026-03-29 (4 agentes, dead code + calidad + consistencia)
> **Plan QA exhaustivo:** 2026-03-30 (172 test cases, 210+ salidas, 15 hallazgos UX)
> **Sistema OCs:** 2026-03-28 (tabla oc_prefixes + OCSelector componente)
> **Pytest suite:** 2026-03-30 (301 tests, 298 passed, 15 módulos, mocks completos)
> **Sesión bugs+features:** 2026-03-31 (15 commits, 18 bugs, 3 features, prompt IA, dual moneda)
> **Última actualización:** 2026-03-31

---

## ✅ COMPLETADO (Producción activa)
- [x] **Multi-tenant completo** (companies, permisos por empresa)
- [x] **PWA con cámara móvil** (instalable, capture camera, offline)
- [x] **Moneda extranjera + IVA** (IA detección, tasa histórica, IVA reclamable)
- [x] **Estadísticas completas** (gráficos, filtros, export PDF)
- [x] **PostgreSQL producción** (Railway deploy activo)
- [x] Sistema cierre proyectos (Excel + emails múltiples)
- [x] Selector emails chips profesional
- [x] Compresión automática imágenes (>3MB)
- [x] Email styled dark theme (Brevo API)
- [x] 21 endpoints API REST
- [x] Auth JWT + roles (ADMIN/BOSS/WORKER)
- [x] Deploy Railway + Vercel
- [x] **Módulo Proveedores completo** (6 fases: BD, IA, 23 endpoints, UI admin, portal, integración)
- [x] **Testing automatizado proveedores** (2026-03-16: 25 issues encontrados)
- [x] **Cloudinary fixes proveedores** (2026-03-17):
  - [x] Borrado archivos Cloudinary al eliminar factura (PDF + páginas)
  - [x] Fix páginas PDF subiendo a raíz en vez de `dazz-suppliers/pages/{supplier_id}/`
  - [x] Fix `delete_invoice_pdf` recibía URL en vez de public_id — usar `extract_public_id_from_url`
- [x] **Fixes varios proveedores** (2026-03-18):
  - [x] Descarga PDF fuerza download (fetch+blob) en vez de abrir en navegador
  - [x] Nombre descarga PDF: `{proveedor}_{fecha}_{numero}.pdf`
  - [x] Eliminar dominio legacy `producciones.dazzcreative.com` (CORS + email fallback)
  - [x] `extract_public_id_from_url` busca solo 'upload', no 'raw' (fix URLs /raw/upload/)
  - [x] `delete_invoice_pdf` añade extensión .pdf al public_id para raw resources
  - [x] Quitar badge "IA ok" de lista facturas en SupplierDetail
  - [x] Endpoint `PUT /{supplier_id}/reactivate` + botón Activar/Desactivar dinámico
- [x] **UI Admin proveedores completa** (2026-03-18):
  - [x] Tamaños estandarizados: títulos 22px Bebas, cuerpo 13px, labels 11-12px, botones 13px
  - [x] Kanban eliminado de InvoicesList
  - [x] Badge EQUIPO eliminado
  - [x] Botón "Ver →" eliminado de SuppliersList (fila clickable)
  - [x] Papelera 34x34px cuadrada
  - [x] Botón Aprobar amber sólido
  - [x] Filas factura: OC + fecha separados, sin texto campaña
  - [x] IBAN en una línea (whitespace-nowrap)
  - [x] OC badge 12px en InvoiceDetail
- [x] **Responsive móvil admin proveedores** (2026-03-18):
  - [x] SuppliersLayout: sidebar hidden móvil + bottom nav 5 items
  - [x] SuppliersDashboard: grid cols-1 móvil
  - [x] SuppliersList: cards móvil + chips empresa scrollables pegadas a bordes
  - [x] InvoicesList: cards móvil con acciones inline
  - [x] SupplierDetail: grid apilado + cards facturas + chips filtro scrollables
  - [x] SupplierInvite: grids cols-1 móvil
  - [x] SupplierNotifications: título 22px
- [x] Setup Claude Code + .claude/ estructura
- [x] Análisis completo proyecto

### ✅ Fixes proveedores completados (verificado en código 2026-03-18):
- [x] **C-1: Encriptar IBAN** - Fernet AES-128 implementado en `encryption.py`, `supplier_portal.py:161` lo usa
- [x] **C-2: Fix file stream upload** - `await file.read()` correcto en `supplier_portal.py:351`
- [x] **C-3: Rate limiting registro** - `@limiter.limit` en validate (10/min), register (5/h), login (5/min)
- [x] **H-1/H-2: N+1 queries** - joinedload + batch aggregation en `suppliers.py:189-230`
- [x] **H-4: Magic bytes PDF** - `validators.py:369` verifica `%PDF`
- [x] **H-5: Sanitizar filename** - `sanitize_filename()` en `validators.py:384-403`
- [x] **H-6: Logout autenticado** - `Depends(get_current_active_supplier)` en `supplier_portal.py:255`
- [x] **H-7: Enum validation status** - `Literal["APPROVED","PAID","REJECTED"]` en `supplier_schemas.py:90`

### ✅ Sprint 1 (Optimizaciones) - COMPLETADO:
- [x] **Optimizar queries backend** (50+ queries → 5-7 queries, 85% reducción)
- [x] **Code splitting frontend** (Bundle 893 KB → 332 KB, 63% reducción)
- [x] **Refactorizar Statistics.jsx** (892 líneas → 13 archivos modulares)
- [x] **Código duplicado backend** (permissions.py centralizado)

---

## ✅ Fixes CRITICAL seguridad — Completados 2026-03-18

- [x] **SEC-C1: Encryption fallback silencioso a plaintext** — `encryption.py:28-33` RuntimeError si falta ENCRYPTION_KEY en producción
- [x] **SEC-C2: Email case-sensitivity en autenticación** — 6 puntos normalizados a `.lower()` en auth.py y routes/auth.py
- [x] **SEC-C3: Timing attack para enumeración de usuarios** — `_DUMMY_HASH` + `pwd_context.verify()` cuando usuario no existe
- [x] **SEC-C4: Validación password inconsistente portal proveedores** — Backend: carácter especial requerido en `supplier_schemas.py:181`. Frontend: validación completa en `Register.jsx:37-39`

---

## ✅ Fixes HIGH seguridad — Completados 2026-03-18

- [x] **SEC-H1: Access token TTL 24h → 30min** — `auth.py:26` default cambiado a 30 min. Refresh token 7 días intacto.
- [x] **SEC-H2: Account lockout tras login fallidos** — Columnas `failed_login_attempts` + `locked_until` en User. Bloqueo 15 min tras 5 intentos. Reset en login exitoso.
- [x] **SEC-H3: Revocar refresh tokens al cambiar password** — `revoke_all_user_refresh_tokens()` llamado tras commit en set-password.
- [x] **SEC-H4: Tokens JWT en localStorage (decisión documentada)** — No migrar a cookies HttpOnly ahora. Riesgo XSS real muy bajo. Documentado en `main.py:59-70`.
- [x] **SEC-H5: PII hasheado en logs** — `_hash_pii()` SHA-256[:12] en `critical_logger.py`. Emails y PII en details hasheados.
- [x] **SEC-H6: Endpoints test protegidos (verificado)** — Ya seguros: ENVIRONMENT defaulta a "production". Documentado en `main.py:133-137`.

## ✅ Fixes HIGH rendimiento — Completados 2026-03-18

- [x] **PERF-H1: Statistics sumas SQL (parcial)** — `_calc_overview()` migrada a `func.sum()`. Funciones restantes necesitan parseo de date String → documentado como aceptable con <500 tickets/año.
- [x] **PERF-H2: Exchange rate caché** — Dict `{(currency, date_str): (rate, timestamp)}` con TTL 1h en `exchange_rate.py`. También migrados prints a logger.
- [x] **PERF-H3: Database connection pool** — `config/database.py` (el correcto) con `pool_size=5, max_overflow=10, pool_pre_ping=True, pool_recycle=300`.
- [x] **PERF-H4: Bundle chunks optimizados** — `vite.config.js` chunks separados para axios (http-vendor) y lucide-react (icons-vendor).

## ✅ Fixes HIGH UX — Completados 2026-03-18

- [x] **UX-H1: alert() → toast notifications** — Sonner instalado. 35 alert() reemplazados en 11 archivos. `<Toaster>` en App.jsx con tema zinc/amber. Portal proveedores: 1 alert → error state inline.
- [x] **UX-H2: Error Boundary** — `ErrorBoundary.jsx` en ambos frontends. Envuelve Routes en App.jsx. Fallback UI con botón "Recargar página".

---

## ✅ Fixes MEDIUM seguridad — Completados 2026-03-18

- [x] **SEC-M1: IBAN validación mod-97** — `validate_iban_format()` en `validators.py`. Llamada antes de cifrar en `supplier_portal.py:159-161`.
- [x] **SEC-M2: HTML escape en emails** — `html.escape()` en 8 puntos de interpolación en `email.py` y `supplier_email.py`.
- [x] **SEC-M3: Token reset — replaceState + meta referrer** — `SetPassword.jsx:24` elimina token de URL con `window.history.replaceState()`. Meta tag `no-referrer` como capa extra.
- [x] **SEC-M4: CSRF (documentado como no necesario)** — Bearer tokens en header, no cookies. CSRF no aplica. Documentado en `main.py:59-70`.
- [x] **SEC-M5: Regex SQL injection eliminada** — Llamada removida de `validate_string_input()`. Función marcada DEPRECATED. ORM es la protección real.

## ✅ Fixes MEDIUM rendimiento — Completados 2026-03-18

- [x] **PERF-M1: asyncio.to_thread para I/O bloqueante** — 6 operaciones wrapeadas: AI extraction, Cloudinary upload, R2 upload, exchange rate API en `supplier_portal.py` y `tickets.py`.
- [x] **PERF-M2: Índices compuestos BD** — `ix_supplier_invoices_supplier_status` y `ix_notifications_recipient_read` en modelos + CREATE INDEX IF NOT EXISTS en startup.
- [x] **PERF-M3: Dashboard re-renders (ya resuelto)** — localStorage se lee una vez en mount. No necesitaba cambio.
- [x] **PERF-M4: Recharts chunks** — Separado en `chart-vendor` chunk en `vite.config.js`.
- [x] **PERF-M5: LIKE aceptable** — Documentado con comentario en `suppliers.py:511-512`. <1000 registros, LIKE secuencial OK.
- [x] **PERF-M6: Statistics _calc_overview SQL** — `func.sum()` + `func.coalesce()` en `statistics.py:272-301`. Endpoint `/overview` también optimizado sin quarter.

## ✅ Fixes MEDIUM lógica — Completados 2026-03-18

- [x] **LOGIC-M1: supplier_type Literal** — `InviteRequest:34` → `Literal["talent","general","mixed"]`. `SupplierUpdate:78` → `Literal["INFLUENCER","GENERAL","MIXED"]`.
- [x] **LOGIC-M2: date_parsed en ORM** — `Column(Date)` en `suppliers.py:122`. Raw SQL reemplazado por ORM en `supplier_portal.py:446`. ALTER TABLE en startup.
- [x] **LOGIC-M3: Race condition cierre proyecto** — `with_for_update()` en `projects.py:217`. Check post-lock `status == CERRADO → 409 Conflict`.
- [x] **LOGIC-M4: Cleanup Cloudinary si falla commit BD** — try/except alrededor de commit en `tickets.py:146-157` y `supplier_portal.py:434-441`. Cleanup con delete_ticket_files/delete_invoice_pdf.
- [x] **LOGIC-M5: Logging en borrado Cloudinary** — `except Exception: pass` → `except Exception as e: logger.error(...)` en `suppliers.py:722,737,740`.
- [x] **LOGIC-M6: Year validación** — `ge=2000, le=2100` en 5 endpoints de `statistics.py` + endpoint `/complete`.

## ✅ Fixes MEDIUM deuda técnica — Completados 2026-03-18

- [x] **DEUDA-M1: print() → logging (parcial)** — `log_config.py` creado con `setup_logging()`. Migrados: `main.py` (5 prints), `routes/auth.py` (26 prints), `services/email.py` (8 prints), `exchange_rate.py` (7 prints). Quedan ~60 prints en otros archivos (futuro sprint).
- [x] **DEUDA-M2: Password validator centralizado** — `_validate_password_strength()` en `schemas.py`. UserCreate y SetPasswordRequest lo referencian.
- [x] **DEUDA-M3: Roles enum (parcial)** — `permissions.py` usa `UserRole.ADMIN/BOSS` en vez de strings. Frontend: `constants/roles.js` con `ROLES` importado en 7 archivos. Quedan `statistics.py`, `projects.py`, `auth.py` backend (futuro sprint).

---

## ✅ Fixes LOW — Completados 2026-03-18

- [x] **SEC-L1: HSTS preload** — `main.py:51` incluye `preload` directive.
- [x] **SEC-L2: Phone validation** — `validators.py:266-271` exige mínimo 9 dígitos efectivos.
- [x] **PERF-L1: localStorage Dashboard (ya resuelto)** — Se lee una vez en mount con `useEffect([], [])`. No necesitaba cambio.
- [x] **UX-L1: Warning cambios sin guardar** — `ReviewTicket.jsx` `initialTicketRef` + `beforeunload` handler cuando hay diff.
- [x] **UX-L2: Escape cierra modales (parcial)** — Hook `useEscapeKey.js` creado. Integrado en `ConfirmDialog.jsx` (cubre todos los confirms) y lightbox de `ReviewTicket.jsx`. Modales restantes en futuro sprint.
- [x] **UX-L3: Labels htmlFor** — `Login.jsx` (suppliers): 2 inputs con id+htmlFor. `Register.jsx`: 7 inputs con id+htmlFor en 3 steps.
- [x] **DEUDA-L1: DazzLogo componente** — `DazzLogo.jsx` en ambos frontends. `Navbar.jsx` y supplier `Login.jsx` lo usan.
- [x] **DEUDA-L2: Constantes de roles** — `constants/roles.js` con ROLES. Importado en 7 archivos: Dashboard, Navbar, ProtectedRoute, Users, ProjectView, StatisticsFilters, useStatisticsData.

---

## ✅ Fixes MEDIUM proveedores (del testing 2026-03-16) — Resueltos via auditoría

- [x] **M-11:** Índice compuesto `(supplier_id, status)` — Cubierto por PERF-M2
- [x] **M-12:** Índice compuesto `(recipient_type, recipient_id, is_read)` — Cubierto por PERF-M2
- [x] **M-14:** supplier_type Literal enum — Cubierto por LOGIC-M1
- [x] **M-18:** File copy async — Cubierto por PERF-M1
- [x] **M-13:** NIF matching: usa `_normalize_nif()` compartida de supplier_ai.py (2026-03-23)
- [x] **M-15:** OC_PENDING invoices: proveedor puede solicitar borrado (PENDING + OC_PENDING) (2026-03-23)
- [x] **M-16:** Atomicidad: file_pages + date_parsed + notificaciones en 1 commit atómico (2026-03-23)
- [x] **M-17:** DELETE_REQUESTED en transition table + mensajes claros por estado terminal (2026-03-23)

## ✅ Sesión 2026-03-28/29 — Auditoría v2 + Sistema OCs (23 commits)

### ✅ Bugs y features pre-auditoría
- [x] **BUG-24:** Upload atómico + cleanup Cloudinary mejorado (PDF + páginas)
- [x] **BUG-27:** Reject deletion request — endpoint + UI en 3 sitios + botón "↩ Rechazar"
- [x] **BUG-28:** Media type normalization completa para IA (JPEG/JPG/HEIC/WebP)
- [x] **ADM-1:** Smart notification routing + delete sin modal + "Limpiar leídas"
- [x] Pending bank cert PDF visible en card IBAN change
- [x] Response param añadido a todos los endpoints rate-limited

### ✅ Auditoría v2 — Seguridad (corregidos 2026-03-28)
- [x] **#1:** Rate limiter auth.py usaba get_remote_address (IP proxy) → importa shared limiter
- [x] **#4:** Timing attack login proveedor → _DUMMY_HASH implementado
- [x] **#6:** Email usuario no normalizado al actualizar → .lower()
- [x] **#7:** Refresh tokens no revocados al cambiar password vía admin → revoke implementado
- [x] **#17:** Log login fallido con IP proxy → get_real_client_ip(request)
- [x] **#18:** Email proveedor no normalizado al registrarse → .lower()
- [x] **#20:** Password Temporal123! hardcodeada → backend genera secrets.token_urlsafe(16)
- [x] **#31:** WORKER can_modify_project sin check empresa → company_ids check añadido
- [x] **#41:** ENVIRONMENT expuesto en endpoint / público → eliminado
- [x] **#43:** IBAN completo en lista proveedores → _mask_iban() primeros 4 + últimos 4
- [x] **#1-stats:** BOSS veía stats de todas empresas en 3 endpoints → filtro company añadido
- [x] **#8-stats:** Usuario sin empresa podía crearse → company_ids obligatorio en UI

### ✅ Auditoría v2 — Rendimiento (corregidos 2026-03-28)
- [x] **#2:** ProjectCard/SearchAndFilters dentro de Dashboard → movidos fuera (evita remount)
- [x] **#8/#9:** 9 índices faltantes en Projects, Tickets, SupplierInvoices, Notifications
- [x] **#10:** N+1 en tickets GET/PUT/DELETE → joinedload(Ticket.project)
- [x] **#11:** N+1 en OC suggestions → joinedload(SupplierOC.company, Project.owner_company)
- [x] **#13:** Sin lazy loading portal proveedores → React.lazy() en 6 páginas
- [x] **#14:** Modelo Claude inconsistente → CLAUDE_MODEL constante unificada
- [x] **#15:** Registro usuario 3 commits → flush() + un commit atómico
- [x] **#22:** AuthContext value sin useMemo → useMemo([user, loading])
- [x] **#23:** Dashboard filtros sin memoización → useMemo en filteredProjects, allStats
- [x] **#24:** Navbar JSON.parse(localStorage) → useAuth() + logout revoca tokens
- [x] **#25:** SuppliersLayout polling por pathname → [] con interval 30s
- [x] **#26:** beforeunload listener cada keystroke → useRef estable con []
- [x] **#36:** Read-modify-write tickets_count/total_amount → SQL atómico con update()
- [x] **#38:** handleInvoiceAction sin loading guard → invoiceActing state + disabled
- [x] **#42:** MD5 para file hash → SHA-256 + columna String(64)
- [x] **#44:** geo_classification e is_foreign sin índice → index=True añadido
- [x] **#45:** browser-image-compression siempre en bundle → dynamic import

### ✅ Auditoría v2 — Calidad (corregidos 2026-03-28)
- [x] **#19:** 9 console.log en ReviewTicket.jsx → eliminados + esbuild drop debugger
- [x] **#27:** _notify() duplicado en 2 archivos → notifications.py compartido (28 callers)
- [x] **#28:** _generate_token() cuadruplicado → canónica en services/auth.py
- [x] **#29:** Markdown stripping triplicado → strip_markdown_json() compartido
- [x] **#30:** Migraciones silencian errores → logger.warning()
- [x] **#33/#34/#35:** Dead code eliminado — companies_service (3 funciones), validators (1), supplier_ai (1)
- [x] **#46:** Statistics.jsx.old backup commiteado → eliminado
- [x] **#48:** localStorage.clear() agresivo → removeItem selectivo
- [x] **#49/#50/#51:** Imports/exports no usados → closeProject, closeProjectWithDownload, useEffect
- [x] **#52:** Ternarias currency inline → getCurrencySymbol() ya importado
- [x] **#4-q/#7-q/#9-11-q/#12-q:** except Exception: pass → logger.error/warning en 4 archivos
- [x] **Imports unused** tras refactor: string en auth.py, secrets+string en suppliers.py y supplier_auth.py

### ✅ Sistema OCs completo (2026-03-28/29)
- [x] **OC-1:** Tabla oc_prefixes en BD — 13 prefijos con company_id, billing_company_id, number_digits, year_format, permanent_oc
- [x] **OC-2:** OC_PREFIX_MAP hardcodeado eliminado → query BD con longest-prefix-match
- [x] **OC-3:** oc-suggestions ya devuelve company_name (sin cambios necesarios)
- [x] **OC-4:** SupplierInvite → OCSelector permanentOnly (solo MGMTINT, campo número)
- [x] **OC-5:** InvoiceDetail → eliminado "Crear nuevo OC", solo buscar existentes
- [x] **OC-6:** ProjectCreate → OCSelector vinculado a empresa del proyecto
- [x] **OC-AUTO:** AutoInvoice → OCSelector 3 pasos reemplaza input libre
- [x] **OCSelector.jsx:** Componente compartido — 3 pasos, props estilo, permanentOnly
- [x] **Endpoints nuevos:** GET /ocs/prefixes + GET /ocs/validate-oc
- [x] **OC-fixes:** permanentOnly autoselecciona, estilos consistentes, label empresa renombrado

### ✅ Sesión 2026-03-29/30 — Autofactura + Auditorías v3/v4 + Portal UI

#### Autofactura completa
- [x] **Lightbox preview PDF** en AutoInvoice (iframe blob URL + X + "Generar y enviar")
- [x] **Pantalla confirmación** tras generar (proveedor, OC, total, descarga PDF, nueva autofactura)
- [x] **Auto-proyecto MGMTINT** para prefijos permanent_oc=True
- [x] **Error 400** para OC no-permanente sin proyecto existente
- [x] **Duplicate check** invoice_number con SELECT FOR UPDATE → 409
- [x] **Cloudinary async** autoinvoice con asyncio.to_thread
- [x] **Transacción atómica** flush + único commit (invoice + notificaciones + proyecto)
- [x] **Response ampliado** con supplier_name, oc_number, invoice_number
- [x] **Hint última factura** registrada solo cuando prefix es permanent_oc
- [x] **allowExisting** prop en OCSelector para autofactura (OC permanente existente = válido)

#### Validaciones IA tickets (T1/T2/T3/T5)
- [x] **T1:** Math check base+IVA-IRPF ≈ total (±MATH_TOLERANCE)
- [x] **T2:** Confidence < MIN_AI_CONFIDENCE → warning
- [x] **T3:** Campos obligatorios (provider, date, final_total) → warning
- [x] **T5:** Error tickets no suman a proyecto (ni count ni total)
- [x] **Badge ⚠️** en ProjectView junto al tipo cuando ticket.notes tiene contenido
- [x] **Banner warnings** en ReviewTicket (azul→amber con lista de warnings)

#### UI Portal desktop + móvil
- [x] **ProjectCreate:** empresa izquierda, OC derecha
- [x] **Portal márgenes:** pt-4 lg:pt-0 en 7 páginas (Home, Upload, Notifications, Profile, ChangeIban, EditData, RequestDeactivation)
- [x] **Notificaciones punto** sin número en sidebar, topbar y bottom nav

#### Auditoría v3 (post-OC/autofactura) — 4 fixes
- [x] **Race condition registro:** with_for_update() en query invitación
- [x] **Imports muertos autoinvoice:** save_invoice_pdf, resolve_company_from_oc eliminados
- [x] **Registro atómico:** 2 commits → flush + 1 commit
- [x] **Console.logs PWA:** 3 eliminados

#### Auditoría calidad v4 — refactors
- [x] **Q1:** Notificaciones inline → _notify() en autoinvoice.py (2) + projects.py (1)
- [x] **Q2:** Constantes centralizadas en config/constants.py (MATH_TOLERANCE, MIN_AI_CONFIDENCE, MAX_SUPPLIER_PDF_SIZE)
- [x] **Q7:** Status labels centralizados en constants/invoiceStatus.js (INVOICE_PILL + INVOICE_LABEL)
- [x] **Dead code:** JSONResponse import + logging_config.py (300 líneas) eliminados

#### Bug fixes
- [x] **Claude list response:** isinstance(list) check en claude_ai.py (BUG-1)
- [x] **Extensiones/MIME types:** +6 MIME types, +3 extensiones, lowercase normalize (BUG-2)
- [x] **Cloudinary subfolders:** tickets en /pdfs/, /pages/, /images/ (BUG-3)
- [x] **Cloudinary folder structure:** folder como parámetro explícito, OC como nombre carpeta, uuid para unicidad
- [x] **Proveedores folder:** nombre proveedor como slug en vez de ID
- [x] **LIM-5:** extra_data en NotificationResponse schema
- [x] **O-1:** Autofactura cleanup Cloudinary si commit falla
- [x] **O-2:** Cert bancario cleanup R2 si commit falla
- [x] **Extension fallback:** inferir extensión de content_type cuando filename no tiene extensión

#### Dead code cleanup masivo (23 items)
- [x] 4 imports backend (BytesIO x2, shutil, extract)
- [x] 7 funciones validators.py nunca llamadas
- [x] 1 función geographic_classifier.py (get_geo_badge_color)
- [x] 4 exports api.js (stats legacy reemplazadas por getCompleteStatistics)
- [x] 2 utils (showInfo, formatAmount)
- [x] 2 archivos portal (Navbar.jsx, BottomNav.jsx)
- [x] 3 imports portal (Link, supplier x2)

---

## 🔵 Fixes LOW proveedores pendientes

- [ ] **L-19:** onupdate lambda: incluir updated_at explícito en bulk updates
- [ ] **L-20:** Logout idempotente: devolver 200 en double logout
- [ ] **L-21:** Dead code: eliminar validación password duplicada en schema
- [ ] **L-22:** TODO misleading: reemplazar con comentario honesto
- [ ] **L-23:** IBAN masking: validar formato antes de enmascarar
- [ ] **L-24:** Math tolerance: usar % en vez de fijo 2 céntimos
- [ ] **L-25:** Admin notifications: documentar convención recipient_id=0

---

## ⏸️ Aparcados (esperando abogado)

Estos issues requieren contenido legal que debe redactar un abogado especialista en protección de datos. No son técnicos — son documentales/legales.

- [ ] **RGPD-C1: Política de privacidad** — Crear páginas `/privacy-policy` y `/terms` en ambos frontends. Enlazar en registro proveedores (`Register.jsx:219` apunta a `href="#"`). Contenido legal pendiente de redacción.
- [ ] **RGPD-C2: Consentimiento insuficiente proveedores** — Separar checkboxes, crear páginas legales, guardar evidencia con timestamp. Depende de RGPD-C1.
- [ ] **RGPD-M1: Endpoint exportación datos personales** — `GET /api/privacy/export` con JSON de datos del usuario. Art. 15/20 RGPD.
- [ ] **RGPD-M2: Procedimiento eliminación de cuenta** — `POST /api/privacy/delete-request` con soft-delete + anonimización. Art. 17 RGPD.
- [ ] **RGPD-M3: Cookie consent banner** — Evaluar si Google Fonts setea cookies. Si sí, implementar banner. Si no, self-hostear fuentes.

---

## 📋 Pendiente futuro sprint

### DEUDA-M1 extendido: Migrar ~60 print() restantes — ✅ 7/7 COMPLETADOS 2026-03-23
- [x] `backend/app/services/cloudinary_service.py` — 16 prints → logger
- [x] `backend/app/routes/projects.py` — 10 prints → logger
- [x] `backend/app/routes/tickets.py` — 4 prints → logger
- [x] `backend/app/routes/suppliers.py` — 4 prints → logger
- [x] `backend/app/routes/users.py` — 3 prints → logger
- [x] `backend/app/services/supplier_storage.py` — 8 prints → logger
- [x] `backend/database_config.py` — 2 prints → logger (2026-03-23)

### DEUDA-M3 extendido: UserRole enum en más archivos backend — ✅ COMPLETADO 2026-03-23
- [x] `backend/app/routes/statistics.py` — 4 strings → UserRole enum
- [x] `backend/app/routes/projects.py` — 2 strings → UserRole enum
- [x] `backend/app/routes/users.py` — 3 strings → UserRole enum
- [x] `backend/app/routes/companies.py` — 2 strings → UserRole enum
- [x] `backend/app/services/auth.py` — 1 string → UserRole enum
- [x] `backend/app/services/companies_service.py` — 3 strings → UserRole enum

### UX-L2 extendido: Escape en modales restantes — ✅ COMPLETADO 2026-03-23
- [x] `frontend/src/pages/suppliers/SupplierDetail.jsx` — editModal + deleteModal
- [x] `frontend/src/pages/suppliers/InvoicesList.jsx` — actionModal
- [x] `frontend/src/pages/suppliers/InvoiceDetail.jsx` — lightbox + rejectModal
- [x] `frontend/src/pages/Users.jsx` — showCreate + showEdit
- [x] `frontend-suppliers/src/pages/Home.jsx` — deleteModal
- [x] Hook copiado a `frontend-suppliers/src/hooks/useEscapeKey.js`

### LOGIC-M2 extendido: Backfill date_parsed — ✅ COMPLETADO 2026-03-23
- [x] Endpoint `POST /suppliers/admin/backfill-date-parsed` — parsea date string → date_parsed para facturas con NULL

---

## 🔧 Bugs generales detectados en testing

- [x] **Bug /health y / endpoint** (500 por slowapi rate limiter) — Fix: `_get_real_client_ip()` custom key function con X-Forwarded-For + fallback (2026-03-23)
- [ ] **Rate limiting no funciona** (workers gunicorn no comparten memoria)
  - storage_uri="memory://" no se comparte entre workers
  - Fix: Usar Redis como backend de rate limiting

## 🔧 Bugs encontrados durante testing manual (2026-03-24)

### Auditoría seguridad v2 — ✅ COMPLETADO 2026-03-23
- 24 issues encontrados: 4 CRITICAL, 7 HIGH, 8 MEDIUM, 5 LOW
- Plan de testing manual generado: `docs/DAZZ_Testing_Plan_v1.pdf` (100 tests)

### Testing manual bloque 1 (T-001 a T-012) — ✅ COMPLETADO 2026-03-24
- 11 bugs encontrados y fixeados durante ejecución:

- [x] **BUG-T1:** Interceptor api.js solo capturaba 401, no 403 — HTTPBearer devolvía 403 sin token
  - Fix: `HTTPBearer(auto_error=False)` → 401 consistente + interceptor solo captura 401
- [x] **BUG-T2:** SetPassword.jsx — token se perdía por re-ejecución de useEffect con `[searchParams]`
  - Fix: `[]` como deps, leer con `new URLSearchParams(window.location.search)`
- [x] **BUG-T3:** Validación password frontend (min 6) desalineada con backend (min 8 + complejidad)
  - Fix: Frontend alineado: 8 chars + mayúscula + número + símbolo
- [x] **BUG-T4:** Password temporal crear usuario `temporal123` → no cumplía validación backend
  - Fix: `Temporal123!`
- [x] **BUG-T5:** Parse errores Pydantic: `detail` es array de objetos → se mostraba `[object Object]`
  - Fix: `Array.isArray(detail) ? detail.map(d => d.msg).join(', ')`
- [x] **BUG-T6:** Interceptor 403 capturaba errores de permisos (non-admin) → loop refresh token
  - Fix: Interceptor solo captura 401. 403 de permisos se propagan normalmente

### Testing manual bloque 2 (T-013 a T-019) — ✅ COMPLETADO 2026-03-24

- [x] **BUG-T7:** WORKER no veía proyectos donde era responsable (query solo usaba owner_id)
  - Fix: `or_(owner_id == user.id, lower(responsible) == username.lower())` en projects.py
- [x] **BUG-T8:** WORKER no podía abrir proyecto donde era responsable (permissions.py solo verificaba owner_id)
  - Fix: `can_access_project` y `can_modify_project` ahora verifican owner_id OR responsible
- [x] **BUG-T9:** Dashboard no cargaba empresas para BOSS/WORKER + empresa no visible en cards
  - Fix: `loadCompanies()` para todos los roles + empresa visible cuando `companies.length > 1`
- [x] **BUG-T10:** Editar usuario enviaba password vacío al backend → 422 Pydantic
  - Fix: Backend `password: Optional[str]` + frontend excluye password vacío del payload
- [x] **BUG-T11:** Autorellenado password browser en modal editar usuario
  - Fix: `autoComplete="new-password"` + `name="new-password"`

### Mejoras implementadas durante testing (2026-03-24)

- [x] Botón "Guardar Cambios" disabled si nada cambió (editHasChanges compara 6 campos)
- [x] Selector responsable filtrado por empresa: `GET /users/usernames?company_id=X`
- [x] BOSS solo ve WORKERs de sus empresas en selector responsable
- [x] Cambiar empresa resetea responsable en ProjectCreate
- [x] Validación backend: responsable debe pertenecer a la empresa del proyecto

---

## 🧪 Sprint 2: Testing & Quality (SIGUIENTE FASE)

### Plan QA generado
- [x] **docs/DAZZ_QA_Testing_Plan.html** — 172 test cases, 32 flujos, 210+ salidas posibles
- [x] Cubre las 3 apps: DAZZ Producciones (70), Admin Proveedores (45), Portal (35), Seguridad (22)

### ✅ Backend tests (pytest) — 301 tests, 298 passed (2026-03-30)
- [x] Setup pytest + conftest.py + fixtures (15 archivos en `backend/tests/`)
- [x] **Auth:** login, JWT, refresh tokens, permisos, lockout, logout (27 tests)
- [x] **Proyectos:** CRUD, permisos, cierre, reopen, delete (24 tests)
- [x] **Tickets:** CRUD + upload completo con mocks Claude/Cloudinary/exchange rate (27 tests)
- [x] **Roles:** RBAC admin/boss/worker (24 tests)
- [x] **Seguridad:** JWT, passwords, headers, error safety (33 tests)
- [x] **Estadísticas:** available-years, overview, monthly, distribution, breakdown (17 tests)
- [x] **Usuarios:** CRUD, permisos, self-deletion (18 tests)
- [x] **Empresas:** GET companies, permisos multi-tenant (9 tests)
- [x] **Schemas:** validaciones Pydantic (29 tests)
- [x] **Permisos:** can_access/can_modify service layer (16 tests)
- [x] **Admin proveedores:** dashboard, lista, detalle, facturas, invitaciones, OCs, notificaciones (30 tests)
- [x] **Portal proveedores:** registro, login, perfil, facturas, summary, account actions (24 tests)
- [x] **Autofactura:** next-number, search, generate, preview, duplicados (10 tests)
- [x] **Regresión:** flujos existentes post-cambios (13 tests)
- [x] **Mocks centralizados:** Claude AI (5 variantes), Cloudinary, R2, exchange rate, email, autoinvoice PDF
- [ ] **test_ocs.py:** tests específicos de OC prefixes (pendiente)
- [ ] **GitHub Actions:** CI/CD automático en push

### Frontend tests (Playwright)
- [ ] **Tests E2E** — Seguir plan en DAZZ_QA_Testing_Plan.html
  - Playwright setup: `npm install -D @playwright/test`
  - App 1: DAZZ Producciones (T-001 a T-070)
  - App 2: Admin Proveedores (T-071 a T-115)
  - App 3: Portal Proveedores (T-116 a T-150)
  - Security cross-app (T-151 a T-172)

### Testing manual
- [ ] Ejecutar plan QA por app: DAZZ → Admin → Portal
- [ ] Documentar resultados en checklist

---

## ✅ Sesión 2026-03-31 — 15 commits, 18 bugs, 3 features

### ✅ Bugs críticos resueltos (2026-03-31)
- [x] **BUG-28:** TicketResponse.date Optional[str] + DateType alias para exchange_rate_date
- [x] **BUG-29:** OC permanente fija empresa DAZZLE MGMT en SupplierInvite
- [x] **BUG-30:** Datos fiscales autofactura — billing_company + company name en auto-created project
- [x] **BUG-32:** Advisory lock pg_try_advisory_lock(12345) para migraciones multi-worker
- [x] **BUG-34:** Drop zone deshabilitada durante upload (opacity + pointer-events-none)
- [x] **BUG-35:** Archivos exitosos se eliminan de files[] automáticamente
- [x] **BUG-37:** cert_type=[object Object] — onClick pasaba SyntheticEvent → arrow function
- [x] **BUG-38/41:** Google Docs Viewer eliminado (0 sitios) → iframe directo + galería img
- [x] **BUG-39:** ia_warnings separado de notes — nueva columna BD + migración + UI separada
- [x] **BUG-40:** Mensaje "Procesado · Pendiente de revisión" en resultados upload
- [x] **BUG-43:** Pending actions 404 — quitado is_read filter, usa PENDING_TITLES
- [x] **BUG-43b:** Banner data change muestra actual vs nuevo con labels español
- [x] **BUG-43c:** IBAN nuevo enmascarado ••••XXXX en banner
- [x] **BUG-43d:** Lightbox certificado con barra superior + botón descarga
- [x] **BUG-44:** Notificación IBAN mismatch movida post-flush con invoice_id
- [x] **BUG-46:** PDF autofactura traducido a inglés (SELF-BILLING INVOICE)
- [x] **BUG-48:** Badge "AUTO" azul en InvoicesList (móvil + desktop)
- [x] **BUG-49:** Autofacturas clickables en portal (tab Received)
- [x] **BUG-50:** exchange_rate_date type shadow — import date as DateType (hotfix producción)

### ✅ Features implementadas (2026-03-31)
- [x] **FEAT-01:** Modal editar proyecto en ProjectView (9 campos, UserAutocomplete, save disabled sin cambios)
- [x] **FEAT-02:** Gastos en autofactura (schema + backend + PDF EXPENSES + UI colapsable)
- [x] **FEAT-03:** Verificado ya implementado — autofacturas PENDING con approve workflow

### ✅ Mejoras IA y UI (2026-03-31)
- [x] **MEJORA-02:** Prompt IA mejorado — Staff Charge ≠ IVA, importes en divisa original, no convertir a EUR
- [x] **MEJORA-03:** Desglose dual moneda en ReviewTicket — editar en divisa original, EUR en tiempo real

### Descartados (ya resueltos)
- [x] **BUG-33:** SHA-256 ya filtra por project_id — no necesita cambio
- [x] **BUG-36:** OC huérfano no aplica — creative_code es string, no FK
- [x] **BUG-51:** Total proyecto — backend ya resta correctamente con SQL atómico
- [x] **BUG-31:** CORS autofactura — configuración correcta, no es bug

### ✅ Bugs previos resueltos
- [x] **BUG-25:** IA rechaza OCs válidos → allowExisting prop en OCSelector (2026-03-30)
- [x] **Race condition autofactura:** SELECT FOR UPDATE en invoice_number (2026-03-29)
- [x] **Cloudinary síncrono autoinvoice:** asyncio.to_thread (2026-03-29)
- [x] **register_supplier() 3 commits:** flush + 1 commit atómico (2026-03-29)
- [x] **generate_autoinvoice() 2 commits:** flush + 1 commit atómico (2026-03-29)

---

## 🔧 Bugs pendientes

- [ ] **Rate limiting storage memory://:** No se comparte entre workers gunicorn — necesita Redis
- [ ] **BUG-47:** Verificar límite tamaño archivos en producción
- [ ] **BUG-52:** Total proyecto huérfano tras error BUG-50 — verificar y limpiar datos producción

---

## 📋 Próxima fase

### Verificar en producción (2026-03-31)
- [ ] Tickets US con Staff Charge — prompt IA mejorado
- [ ] Autofacturas con gastos — sección EXPENSES en PDF
- [ ] Modal editar proyecto — permisos ADMIN/BOSS
- [ ] Badge AUTO en lista facturas admin
- [ ] Autofactura clickable en portal proveedores
- [ ] Lightbox certificado bancario con descarga

### Integraciones pendientes
- [ ] **INT-1:** Facturas aprobadas proveedores → tickets en DAZZ Producciones (ya parcial en approve endpoint)

### Testing
- [ ] **test_ocs.py:** 34 tests creados, pendiente fix conftest para ejecutar
- [ ] **GitHub Actions:** CI/CD automático en push
- [ ] **Playwright E2E:** Setup + flujos críticos
- [ ] Testing manual plan QA por app

---

## ✅ Calidad completada (auditoría v4 — 2026-03-30)

- [x] **Q1:** _notify() unificado en autoinvoice.py + projects.py
- [x] **Q2:** Constantes centralizadas (MATH_TOLERANCE, MIN_AI_CONFIDENCE, MAX_SUPPLIER_PDF_SIZE)
- [x] **Q3:** Company invoice_prefix en BD (columna + migración startup + seed idempotente) — reemplaza if/elif hardcodeado
- [x] **Q4:** window.confirm → ConfirmDialog en Users.jsx (eliminar usuario)
- [x] **Q5:** ~~Error messages EN/ES~~ — Investigado: admin=ES, portal=EN, ya correctamente separados
- [x] **Q6:** Password validation DRY — password_validator.py compartido con lang="es"/"en"
- [x] **Q7:** Status labels centralizados en constants/invoiceStatus.js
- [x] **Q9:** AutoInvoice fecha en-GB → es-ES
- [x] **Q10:** ~~Emails hardcodeados~~ — Ya usan os.getenv() con defaults, no requiere cambios

## ✅ Hallazgos Plan QA (2026-03-30) — 13 de 15 implementados

### Implementados (3 commits)
- [x] **F-001:** Ruta 404 catch-all en DAZZ Producciones (NotFound component)
- [x] **F-002:** Login redirige usuarios ya autenticados a /dashboard
- [x] **F-003:** Botones Users.jsx con loading state (submitting, disabled, "Guardando...")
- [x] **F-004:** Drop zone filtra por MIME type al arrastrar (solo JPG/PNG/WebP/HEIC/PDF)
- [x] **F-005:** EditData portal muestra error en non-401 (antes silenciaba)
- [x] **F-006:** Notifications portal rollback optimista si API falla (.catch)
- [x] **F-007:** Dashboard + Layout admin muestran banner error si API falla
- [x] **F-009:** ReviewTicket beforeunload con tolerancia numérica (0.01€) para floats
- [x] **F-010:** Login muestra mensaje específico de bloqueo en 429
- [x] **F-011:** Upload portal sin IBAN → enlace a /profile/change-iban (antes mandaba a email)
- [x] **F-012:** Home portal distingue error de carga (retry) vs sin facturas
- [x] **F-013:** OCSelector mensaje cuando no hay prefijos para la empresa
- [x] **F-015:** ~~Botón autofactura~~ — Ya implementado (sending state existía)
- [x] **F-016:** Notificaciones IA_REJECTED vinculadas al supplier_id tras registro

### Descartados intencionalmente
- [ ] **F-008:** ProjectCloseReview window.confirm — Se queda como está (flujo ya tiene validación previa)
- [ ] **F-014:** Statistics PDF solo exporta internacional — Es el diseño deseado (informe IVA)

---

## 💡 Sprint 3: Features Nuevas (después de testing)

- [ ] **INT-1:** Facturas aprobadas → proyectos DAZZ (integración completa tickets — AL FINAL)
- [ ] **Notificaciones PWA push** (Firebase o OneSignal)
- [ ] **Dashboard analytics** (métricas uso, engagement, performance)
- [ ] **Búsqueda avanzada global** (proyectos, tickets, proveedores)
- [ ] **Filtro por año / archivado proyectos**
- [ ] **FUT-1:** WebSockets notificaciones (reemplazar polling)

---

## 🔮 Backlog Futuro (3+ meses)
- [ ] OCR avanzado (PDF facturas complejas multipágina)
- [ ] Integración contabilidad (Contaplus, A3, Sage)
- [ ] API pública REST (webhooks, integraciones terceros)
- [ ] Roles granulares (permisos custom por usuario)
- [ ] Audit log completo (quién hizo qué cuándo)
- [ ] TypeScript migration (frontend)

---

## 📝 Criterios Priorización

**ROI = Impacto / Esfuerzo**

**Impacto:**
- ⭐⭐⭐⭐⭐ Crítico (calidad, confiabilidad, seguridad)
- ⭐⭐⭐⭐ Alto (performance, UX, productividad)
- ⭐⭐⭐ Medio (mejora notable)
- ⭐⭐ Bajo (nice to have)

**Esfuerzo:**
- 🔨 Bajo (<2h)
- 🔨🔨 Medio (2-5h)
- 🔨🔨🔨 Alto (5-10h)
- 🔨🔨🔨🔨 Muy alto (10+h)

---

## 🎯 Métricas Éxito

**Sprint 1 (Optimizaciones) — COMPLETADO:**
- Initial bundle: 332KB (mejorado caching con chunks separados - 2026-03-18)
- Statistics render: <100ms ✅ LOGRADO
- Queries BD: <50ms promedio ✅ MEJORADO + SQL aggregations
- Código duplicado: centralizado ✅ LOGRADO

**Auditoría seguridad v1 — COMPLETADO 2026-03-18:**
- 4 CRITICAL + 6 HIGH + 5 MEDIUM + 2 LOW: ✅ TODOS RESUELTOS

**Auditoría seguridad v2 — COMPLETADO 2026-03-28:**
- 53 hallazgos nuevos (7 agentes paralelos)
- 41 resueltos en sesión, 12 pendientes (6 bugs + 6 LOW)
- Sistema OCs: tabla BD + componente UI + 2 endpoints nuevos
- Limpieza: -1080 líneas dead code, 5 funciones duplicadas unificadas

**Sprint 2 (Testing):**
- Backend coverage: 70%+ (actual: tests existen, cobertura por verificar)
- Frontend E2E: 10+ flujos críticos (actual: 0)
- CI/CD: Auto-run tests en PRs

**RGPD Pre-Lanzamiento (esperando abogado):**
- Política privacidad: pendiente redacción legal
- Consentimiento proveedores: pendiente contenido legal
- DPAs firmados: Railway, Cloudinary, Anthropic, Cloudflare — pendiente
- Registro actividades tratamiento: pendiente

---

## 📊 Resumen ejecutivo

| Categoría | Total | Resueltos | Pendientes | Estado |
|-----------|-------|-----------|------------|--------|
| Seguridad CRITICAL | 4 | 4 | 0 | ✅ |
| Seguridad HIGH | 6 | 6 | 0 | ✅ |
| Seguridad MEDIUM | 5 | 5 | 0 | ✅ |
| Seguridad LOW | 2 | 2 | 0 | ✅ |
| Seguridad proveedores | 7 | 7 | 0 | ✅ (SEC-1 a SEC-7) |
| RGPD | 5 | 0 | 5 | ⏸️ Esperando abogado |
| Rendimiento HIGH | 4 | 4 | 0 | ✅ |
| Rendimiento MEDIUM | 6 | 6 | 0 | ✅ |
| Rendimiento LOW | 1 | 1 | 0 | ✅ |
| Lógica MEDIUM | 6 | 6 | 0 | ✅ |
| UX HIGH | 2 | 2 | 0 | ✅ |
| UX LOW | 3 | 3 | 0 | ✅ |
| UX proveedores | 17 | 17 | 0 | ✅ (UX-1 a UX-18) |
| Bugs proveedores | 21 | 20 | 1 | 🟡 (BUG-4 pendiente) |
| Deuda técnica MEDIUM | 3 | 3 (parcial) | 0 | ✅ |
| Deuda técnica LOW | 2 | 2 | 0 | ✅ |
| **Total** | **94** | **85** | **5 RGPD + 4 pendientes** | |

---

## 🚀 Portal Proveedores v2 — Acordado 2026-03-23

### 1. Eliminar tipos de proveedor (INFLUENCER/GENERAL/MIXED) — ✅ COMPLETADO 2026-03-23
- [x] Eliminar enum `SupplierType` y columna del ORM (columna BD se mantiene como dead data)
- [x] Eliminar `supplier_type` de 5 schemas (InviteRequest, SupplierResponse, SupplierUpdate, ValidateTokenResponse, ProfileResponse)
- [x] Añadir `has_permanent_oc` y `company_name` a SupplierResponse y ProfileResponse
- [x] Reescribir `supplier_ai.py` validación OC: lógica unificada (oc_id → OC permanente, sino → proyecto)
- [x] Simplificar `supplier_portal.py`: eliminar supplier_type de registro/login/profile
- [x] Simplificar `routes/suppliers.py`: eliminar de invite/list/update
- [x] Frontend admin: eliminar TYPE_BADGE de SuppliersList, columna "Tipo" de tabla
- [x] Frontend admin: eliminar selector tipo de SupplierDetail modal editar, badge tipo → badge OC
- [x] Frontend admin: reescribir SupplierInvite — checkbox "Crear OC permanente" en vez de 3 tipos
- [x] Portal Profile: eliminar TYPE_BADGE, usar `company_name` del endpoint
- [x] Portal Upload: adaptar texto OC permanente
- [x] Verificación: 0 referencias a SupplierType/INFLUENCER/MIXED en todo el código

### 2. Facturas sin OC — asignación manual por admin — ✅ COMPLETADO 2026-03-23
- [x] Schema `AssignInvoiceOCRequest` en `supplier_schemas.py`
- [x] Endpoint `GET /suppliers/oc-suggestions?q=` — autocompletado OCs permanentes + proyectos abiertos
- [x] Endpoint `PATCH /suppliers/invoices/{id}/assign-oc` — asigna OC, resuelve project/company, OC_PENDING → PENDING
- [x] `suppliersApi.js`: `assignInvoiceOC()` + `getOCSuggestions()`
- [x] `InvoicesList.jsx`: filtro "Sin OC", banner info, highlight filas OC_PENDING (azul), botón "Asignar OC →"
- [x] `InvoiceDetail.jsx`: sección "Asignar OC" con buscador autocompletado + opción texto libre + badge "Sin OC"

### 3. Autofacturación — nueva sección admin — ✅ COMPLETADO 2026-03-23
- [x] Backend: nuevo router `routes/autoinvoice.py` con 4 endpoints (next-number, supplier-search, generate, preview)
- [x] Backend: `services/autoinvoice_pdf.py` — generación PDF con fpdf2 (zero system deps, no LibreOffice)
- [x] Backend: campo `is_autoinvoice` en SupplierInvoice + ALTER TABLE en startup
- [x] Backend: `GET /portal/invoices/received` — portal lista autofacturas recibidas
- [x] Backend: `send_autoinvoice_notification` email al proveedor
- [x] Frontend admin: `AutoInvoice.jsx` — formulario completo con:
  - Selector empresa DAZZ → autocomplete datos fiscales
  - Buscador proveedor → autocomplete nombre/NIF/dirección/IBAN
  - Campos factura: concepto, base, IVA%, IRPF%, fecha, nº factura secuencial, OC
  - Resumen con cálculos en tiempo real
  - Preview PDF (nueva ventana) + Generar y enviar
- [x] Admin sidebar: item "Autofactura" con icono FilePlus
- [x] Portal Home.jsx: pestaña "Received" conectada con endpoint real + cards con diseño azul "Generated by DAZZ"
- [x] `requirements.txt`: fpdf2==2.8.1
- [x] Dependencia: `fpdf2` añadida (5KB, zero system deps)

### 4. Portal Proveedores v2 — UI — ✅ COMPLETADO 2026-03-23
- [x] Layout.jsx: sidebar desktop (196px) + topbar + bottom nav 4 items mobile
- [x] Home.jsx: KPIs + tabs "My invoices" / "Received invoices" (placeholder)
- [x] Notifications.jsx: lista con icons por tipo, unread dots, mark read, filter All/Unread
- [x] Profile.jsx: 2-column desktop, pending change card, 3 action buttons
- [x] EditData.jsx: formulario name/phone/address → submit for review
- [x] ChangeIban.jsx: formulario new IBAN + PDF upload → submit for review
- [x] RequestDeactivation.jsx: formulario con motivo → send request
- [x] App.jsx: 9 rutas (/, /upload, /notifications, /profile, /profile/edit-data, /profile/change-iban, /profile/deactivation, /login, /register)
- [x] Backend: 3 endpoints notificaciones portal (GET /portal/notifications, PUT read, PUT read-all)
- [x] Backend: 3 endpoints account actions (POST request-data-change, request-iban-change, request-deactivation)
- [x] Backend: unread_notifications en SummaryResponse, has_pending_change en ProfileResponse
- [x] Mockup v2 seguido fielmente para todas las pantallas
- [ ] PWA: pendiente configurar `vite-plugin-pwa` (ya configurado — verificar)

### 5. Cambio de datos → revisión admin — ✅ COMPLETADO 2026-03-23
- [x] Edit data: nombre, teléfono, dirección (email y NIF NO editables)
- [x] Change IBAN: nuevo IBAN + nuevo PDF → IBAN actual sigue activo hasta aprobación admin
- [x] Backend: `POST /portal/request-data-change` y `POST /portal/request-iban-change`
- [x] IA valida que IBAN del certificado coincide con IBAN escrito (completado Fase 7/8)
- [ ] Admin: UI para aprobar/rechazar cambios de datos (futuro)

### 6. Solicitud desactivación — ✅ COMPLETADO 2026-03-23
- [x] Botón en Profile → formulario con motivo → endpoint
- [x] Backend: `POST /portal/request-deactivation`
- [x] Datos conservados por ley (6 años Hacienda) — documentado en warning UI

### 7. Validación IA — IBAN en facturas — ✅ COMPLETADO 2026-03-23
- [x] IBAN mismatch cambiado de `errors` (bloqueante) a `warnings` (no bloqueante)
- [x] Campo `iban_match` (true/false/null) añadido al resultado de `validate_supplier_invoice()`
- [x] Notificación admin "IBAN Mismatch" cuando `iban_match=False` en upload_invoice
- [x] Checklist IA en InvoiceDetail admin: ✓ match / ✗ mismatch / — not found
- [x] `ia_validation_result` JSON ya incluye `iban_match` automáticamente

### 8. Validación IA — IBAN en registro — ✅ COMPLETADO 2026-03-23
- [x] Nueva función `extract_iban_from_cert()` en `supplier_ai.py` (Claude, prompt simple)
- [x] Nuevo endpoint `POST /portal/validate-bank-cert` (sin auth, rate-limited 10/h)
- [x] Si IBAN no coincide → 422 bloquea registro
- [x] Si IA no puede leer IBAN → `valid: true` (no bloquea) + notificación admin "manual review recommended"
- [x] Frontend Register.jsx: Step 2 "Continue" → valida IBAN vs cert antes de avanzar a Step 3
- [x] Loading state "Verifying IBAN..." en botón Continue
- [x] Implementado en `routes/supplier_portal.py` — token validación + rate limit 5/h (SEC-2)

---

## ✅ Auditoría seguridad proveedores — Completado 2026-03-27

### Seguridad (7 issues)
- [x] **SEC-1:** IBAN movido de query param a Form body en request-iban-change (GDPR)
- [x] **SEC-2:** Rate limiter unificado en `app/services/rate_limit.py` con `get_real_client_ip` (X-Forwarded-For). validate-bank-cert requiere token invitación + bajado a 5/hour
- [x] **SEC-3:** Campo `iban` eliminado de SupplierInvoice response + schema (IBAN match sigue via ia_validation_result)
- [x] **SEC-4:** `max_length=128` en password de RegisterRequest y LoginRequest (previene DoS bcrypt)
- [x] **SEC-5:** `nif_cif unique=True` en Supplier + partial unique index case-insensitive + validación en registro
- [x] **SEC-6:** `mark_notification_read` filtra por `recipient_type == ADMIN` (no puede marcar notifs de proveedor)
- [x] **SEC-7:** `oc_id unique=True` en Supplier + partial unique index + validación en registro y assign-oc

### Bugs críticos (20 issues)
- [x] **BUG-1:** try/except en 2 llamadas Anthropic API + warning si API key falta
- [x] **BUG-3:** Temp files → `tempfile.NamedTemporaryFile` (usa /tmp en Railway)
- [x] **BUG-5:** Data changes en `extra_data` field de SupplierNotification (no free-text parse)
- [x] **BUG-6:** `pending_bank_cert_url` campo dedicado en Supplier (no parsea mensaje)
- [x] **BUG-7:** `delete_bank_cert()` creada + borrado R2 al rechazar IBAN
- [x] **BUG-8:** Timezone fix en 5 funciones timeAgo (`dateStr + 'Z'` suffix)
- [x] **BUG-9:** Certificado bancario en lightbox iframe con Google Docs Viewer
- [x] **BUG-10:** IBAN normalización (guiones/puntos/espacios) + IBAN opcional en registro + mensaje non-EU
- [x] **BUG-11:** Historial SupplierDetail filtra por `supplier_id` en backend (no 20 globales)
- [x] **BUG-12:** `PENDING_TITLES` constante compartida en `models/suppliers.py`
- [x] **BUG-13:** `currentPage` reset a 0 al navegar entre facturas
- [x] **BUG-14:** initials `.filter(Boolean)` para doble espacio en nombre
- [x] **BUG-15:** localStorage `JSON.parse` en try/catch
- [x] **BUG-16:** `iva_percentage ?? 0` null guard (NaN% fix)
- [x] **BUG-17:** N+1 fix en `list_received_invoices` con `joinedload(company)`
- [x] **BUG-18:** Content-Disposition sanitizado con `re.sub(r'[^\w\s-]', '')`
- [x] **BUG-19:** `backfill_date_parsed` en lotes de 100 con commit por lote
- [x] **BUG-20:** OC_PENDING añadido al filtro status en portal Home
- [x] **BUG-21:** DELETE_REQUESTED → ConfirmDialog/modal custom (no window.confirm)
- [x] **BUG-26:** Banner pending-actions filtra solo PENDING_TITLES (sin IA_REJECTED)

### UX (17 issues)
- [x] **UX-1:** try/catch + showError en handleAddNote y handleDeleteNote
- [x] **UX-2:** try/catch + showError en descarga PDF InvoiceDetail
- [x] **UX-3:** Estado `acting` en handleAction InvoicesList (anti doble-clic)
- [x] **UX-4:** Feedback archivos rechazados (tipo/tamaño) en portal Upload
- [x] **UX-5:** Validación PDF + tamaño en ChangeIban + `finally` para setSending
- [x] **UX-6:** Error state visible en portal Home.jsx (no catch vacío)
- [x] **UX-7:** `showError` en SuppliersList catch (no lista vacía silenciosa)
- [x] **UX-9:** Status badge dinámico en portal Profile (no hardcoded "ACTIVE")
- [x] **UX-10:** STATUS_LABEL español en SuppliersList (ACTIVO/DESACTIVADO/NUEVO)
- [x] **UX-11:** window.confirm → ConfirmDialog en InvoiceDetail DELETE_REQUESTED
- [x] **UX-12:** Paginación con ellipsis en InvoicesList (algoritmo getPageNumbers)
- [x] **UX-13:** timeAgo "0min" → "ahora" en SuppliersList, SupplierDetail, SuppliersDashboard
- [x] **UX-14:** Banner acciones pendientes movido dentro columna derecha SupplierDetail
- [x] **UX-15:** `logger.warning` en email PAID fallido (no `pass` silencioso)
- [x] **UX-16:** Dropzone bloqueado durante análisis IA en Upload ("AI analyzing...")
- [x] **UX-17:** Visor PDF facturas lightbox en portal Home (Google Docs Viewer + navegación)
- [x] **UX-18:** Warning NIF duplicado en SupplierInvite (endpoint GET /ocs/check-nif + onBlur)

---

## 📋 Pendiente — Próximas sesiones

### Bugs pendientes
- [ ] **BUG-4:** Upload loop continúa tras unmount (portal Upload.jsx) — state update on unmounted
- [ ] **BUG-22:** Proveedores sin IBAN — pendiente decisión contabilidad
- [ ] **BUG-23:** Auditoría IA — para el final
- [ ] **BUG-24:** PDF sube a Cloudinary aunque IA falle
- [ ] **BUG-25:** IA rechaza OCs válidos
- [ ] **BUG-27:** Admin no puede rechazar DELETE_REQUESTED

### Admin pendiente
- [ ] **ADM-1:** Borrado notificaciones admin (papelera individual + limpiar leídas)
- [ ] **ADM-3:** Mejoras visuales admin proveedores

### OCs y empresas
- [ ] **OC-1:** Crear tabla oc_prefixes en BD + insertar prefijos 4 empresas
- [ ] **OC-2:** Reemplazar OC_PREFIX_MAP hardcodeado → query a BD
- [ ] **OC-3:** Actualizar oc_suggestions endpoint + campo EMPRESA en InvoiceDetail
- [ ] **OC-4:** SupplierInvite.jsx — selector empresa → tipo → número
- [ ] **OC-5:** InvoiceDetail.jsx — selector empresa → tipo → número al asignar OC
- [ ] **OC-6:** Crear proyecto en DAZZ Producciones — selector empresa → tipo → número

### Limpieza y deuda técnica
- [ ] **LIM-1:** validate_supplier_invoice re-query supplier → pasar objeto
- [ ] **LIM-2:** totalLoaded state nunca se usa en InvoicesList — eliminar
- [ ] **LIM-3:** Array index como key en file list Upload.jsx
- [ ] **LIM-4:** Limpieza código referencias eliminadas

### Rendimiento e integración
- [ ] **REN-1:** Revisión completa rendimiento (especialmente móvil)
- [ ] **INT-1:** Facturas aprobadas → reflejarse en proyectos DAZZ Producciones

### Testing
- [ ] **TEST-1:** Computer Use testing automatizado

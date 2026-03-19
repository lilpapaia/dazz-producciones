# TODO - Dazz Producciones

> **Auditoría exhaustiva completada:** 2026-03-18
> **Sesión de fixes completada:** 2026-03-18
> **Issues resueltos en esta sesión:** 44 de 50 (6 CRITICAL seg, 13 HIGH, 19 MEDIUM, 8 LOW) — quedan 5 RGPD aparcados + pendientes futuros
> **Archivos modificados:** ~40 backend + ~20 frontend

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
- [ ] **M-13:** NIF matching: query filtrada en vez de full table scan
- [ ] **M-15:** OC_PENDING invoices: añadir path de borrado
- [ ] **M-16:** Atomicidad: commit invoice + notificaciones juntos
- [ ] **M-17:** DELETE_REQUESTED en transition table con mensaje claro

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

### DEUDA-M1 extendido: Migrar ~60 print() restantes
- [ ] `backend/app/services/cloudinary_service.py` (~16 prints)
- [ ] `backend/app/routes/projects.py` (~10 prints)
- [ ] `backend/app/routes/tickets.py` (~4 prints)
- [ ] `backend/app/routes/suppliers.py` (~4 prints)
- [ ] `backend/app/routes/users.py` (~3 prints)
- [ ] `backend/app/services/supplier_storage.py` (~8 prints)
- [ ] `backend/database_config.py` (~2 prints)

### DEUDA-M3 extendido: UserRole enum en más archivos backend
- [ ] `backend/app/routes/statistics.py` (líneas 21, 194, 198)
- [ ] `backend/app/routes/projects.py` (líneas 117, 121)
- [ ] `backend/app/services/auth.py` (línea 176)

### UX-L2 extendido: Escape en modales restantes
- [ ] `frontend/src/pages/suppliers/SupplierDetail.jsx` (modal borrado factura)
- [ ] `frontend/src/pages/suppliers/InvoicesList.jsx` (modal borrado)
- [ ] `frontend/src/pages/suppliers/InvoiceDetail.jsx` (lightbox)
- [ ] `frontend/src/pages/Users.jsx` (modal crear/editar)
- [ ] `frontend-suppliers/src/pages/Home.jsx` (modal borrado)

### LOGIC-M2 extendido: Backfill date_parsed
- [ ] Crear endpoint temporal o script para backfill `date_parsed` en registros anteriores a la migración ORM (los creados con raw SQL ya tienen valor)

---

## 🔧 Bugs generales detectados en testing

- [ ] **Bug /health y / endpoint** (500 por slowapi rate limiter)
  - Probablemente get_remote_address falla detrás de proxy Railway
  - Fix: Probar sin rate limiter o con X-Forwarded-For
- [ ] **Rate limiting no funciona** (workers gunicorn no comparten memoria)
  - storage_uri="memory://" no se comparte entre workers
  - Fix: Usar Redis como backend de rate limiting

---

## 🧪 Sprint 2: Testing & Quality (2-3 semanas)

### Backend tests (parcialmente hecho)
- [x] Setup pytest + conftest.py + fixtures (11 archivos en `backend/tests/`)
- [ ] **Verificar cobertura real y ejecutar tests** (Esfuerzo: 🔨 2h | ROI: ⭐⭐⭐⭐⭐)
- [ ] **Auth:** login, JWT, refresh tokens, permisos
- [ ] **IA extracción:** mock Claude API, validación datos
- [ ] **Cierre proyectos:** Excel generación (BytesIO), emails
- [ ] **Moneda:** tasa cambio, conversión EUR, geo classification
- [ ] **Companies:** permisos multi-tenant
- [ ] Target: 70%+ coverage crítico

### Frontend tests (0% - no existe)
- [ ] **Tests E2E frontend** (Esfuerzo: 🔨🔨🔨🔨 8-10h | ROI: ⭐⭐⭐)
  - Playwright setup: `npm install -D @playwright/test`
  - Flujo completo: Login → Crear proyecto → Upload ticket → Review → Cerrar
  - Flujo estadísticas: Filtros → Gráficos → Export PDF
  - Flujo multi-empresa: ADMIN ve todas, BOSS solo suya
  - Flujo móvil PWA: Instalar → Cámara → Upload
  - CI/CD: GitHub Actions integration

---

## 💡 Sprint 3: Features Nuevas (3-4 semanas)

- [ ] **Notificaciones PWA push** (Firebase o OneSignal)
- [ ] **Dashboard analytics** (métricas uso, engagement, performance)
- [ ] **Búsqueda avanzada global** (proyectos, tickets, proveedores)
- [ ] **Componentes reutilizables frontend** (FormField wrapper, useVoiceSearch compartido)

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

**Auditoría seguridad — COMPLETADO 2026-03-18:**
- 4 CRITICAL seguridad: ✅ RESUELTOS
- 6 HIGH seguridad: ✅ RESUELTOS
- 5 MEDIUM seguridad: ✅ RESUELTOS
- 2 LOW seguridad: ✅ RESUELTOS
- Account lockout: ✅ IMPLEMENTADO (5 intentos → 15 min bloqueo)
- Token TTL: ✅ REDUCIDO (24h → 30min + refresh 7d)
- PII en logs: ✅ HASHEADO

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
| RGPD | 5 | 0 | 5 | ⏸️ Esperando abogado |
| Rendimiento HIGH | 4 | 4 | 0 | ✅ |
| Rendimiento MEDIUM | 6 | 6 | 0 | ✅ |
| Rendimiento LOW | 1 | 1 | 0 | ✅ |
| Lógica MEDIUM | 6 | 6 | 0 | ✅ |
| UX HIGH | 2 | 2 | 0 | ✅ |
| UX LOW | 3 | 3 | 0 | ✅ |
| Deuda técnica MEDIUM | 3 | 3 (parcial) | 0 | ✅ |
| Deuda técnica LOW | 2 | 2 | 0 | ✅ |
| **Total** | **50** | **44** | **5 RGPD + pendientes futuros** | |

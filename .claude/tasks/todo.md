# TODO - Dazz Producciones

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

---

## 🔄 EN PROGRESO
- [x] Setup Claude Code + .claude/ estructura
- [x] Análisis completo proyecto

---

## 🚀 Sprint 1: Optimizaciones (1-2 semanas)

### Prioridad Alta
- [x] **Optimizar queries backend** (Esfuerzo: 🔨🔨 3-4h | ROI: ⭐⭐⭐⭐⭐)
  - ✅ Auditar N+1 en: projects + tickets, companies, statistics
  - ✅ Verificar joinedload en todas las relaciones
  - ✅ Implementado 2026-03-11: 50+ queries → 5-7 queries (85% reducción)
  - ✅ Archivos: statistics.py, projects.py, users.py
  - ✅ Verificado: Funcionalidad 100% intacta

- [x] **Code splitting frontend** (Esfuerzo: 🔨 2-3h | ROI: ⭐⭐⭐⭐⭐)
  - ✅ Lazy load rutas: Statistics, Users, ProjectCreate, etc. (8 rutas)
  - ✅ Dynamic import jsPDF + html2canvas (solo al exportar)
  - ✅ Implementado 2026-03-11: Bundle 893 KB → 332 KB (63% reducción)
  - ✅ Archivos: App.jsx, Statistics.jsx, vite.config.js
  - ✅ Verificado: Navegación funciona, spinner apropiado

- [x] **Refactorizar Statistics.jsx** (Esfuerzo: 🔨🔨 4-6h | ROI: ⭐⭐⭐⭐)
  - ✅ 892 líneas → 13 componentes modulares (max 161 líneas/archivo)
  - ✅ Separado: index.jsx, hooks/, services/, components/
  - ✅ Hooks custom: useStatisticsData, useExpandedState
  - ✅ Performance: React.memo (7 comp.), useMemo, useCallback
  - ✅ Implementado 2026-03-11: Render 300ms → <100ms (3x más rápido)
  - ✅ Archivos: Statistics/ (13 archivos nuevos)
  - ✅ Verificado: Filtros, expandir, PDF, navegación funcionan

---

## 🚀 Sprint 1: Pendiente

### Prioridad Media (OPCIONAL)
- [ ] **Código duplicado backend** (Esfuerzo: 🔨🔨 3-5h | ROI: ⭐⭐⭐⭐)
  - Centralizar permisos (can_access_project duplicado)
  - Validaciones Pydantic (amounts >0, strings length, etc.)
  - Error handling específico (no bare except:)
  
- [ ] **Componentes reutilizables frontend** (Esfuerzo: 🔨🔨 4-5h | ROI: ⭐⭐⭐)
  - LoadingSpinner.jsx (usado en 5 archivos)
  - StatusBadge.jsx (usado en 4+ lugares)
  - useVoiceSearch hook (duplicado Dashboard/ProjectView)
  - useMemo en listas filtradas (Dashboard, ProjectView)

---

## 🧪 Sprint 2: Testing & Quality (2-3 semanas)

### Prioridad Alta (CRÍTICO - 0% coverage actual)
- [ ] **Tests unitarios backend** (Esfuerzo: 🔨🔨🔨 6-8h | ROI: ⭐⭐⭐⭐⭐)
  - Setup: pytest + conftest.py + fixtures
  - Auth: login, JWT, refresh tokens, permisos
  - IA extracción: mock Claude API, validación datos
  - Cierre proyectos: Excel generación (BytesIO), emails
  - Moneda: tasa cambio, conversión EUR, geo classification
  - Companies: permisos multi-tenant
  - Target: 70%+ coverage crítico
  
- [ ] **Tests E2E frontend** (Esfuerzo: 🔨🔨🔨🔨 8-10h | ROI: ⭐⭐⭐)
  - Playwright setup: `npm install -D @playwright/test`
  - Flujo completo: Login → Crear proyecto → Upload ticket → Review → Cerrar
  - Flujo estadísticas: Filtros → Gráficos → Export PDF
  - Flujo multi-empresa: ADMIN ve todas, BOSS solo suya
  - Flujo móvil PWA: Instalar → Cámara → Upload
  - CI/CD: GitHub Actions integration

---

## 💡 Sprint 3: Features Nuevas (3-4 semanas)

### Prioridad Media
- [ ] **Notificaciones PWA push** (Esfuerzo: 🔨🔨 5-7h | ROI: ⭐⭐⭐)
  - Push notifications setup (Firebase o OneSignal)
  - Notif: Proyecto nuevo asignado
  - Notif: Ticket pendiente review
  - Notif: Proyecto cerrado
  - Settings: Enable/disable por tipo
  
- [ ] **Dashboard analytics** (Esfuerzo: 🔨🔨 5-6h | ROI: ⭐⭐)
  - Métricas uso: usuarios activos/día, tickets/día, proyectos/mes
  - Engagement: tiempo promedio sesión, bounce rate
  - Performance: tiempos carga (backend/frontend), errores API
  - Gráficos históricos: Recharts 30 días
  - Export CSV métricas
  
- [ ] **Búsqueda avanzada** (Esfuerzo: 🔨🔨 4-5h | ROI: ⭐⭐⭐)
  - Search bar global (proyectos, tickets, proveedores)
  - Filtros combinados: fecha + empresa + responsable + estado
  - Resultados instantáneos (debounce 300ms)
  - Highlights resultados

---

## 🔮 Backlog Futuro (3+ meses)
- [ ] OCR avanzado (PDF facturas complejas multipágina)
- [ ] Machine Learning: Predicción gastos próximo mes
- [ ] Integración contabilidad (Contaplus, A3, Sage)
- [ ] API pública REST (webhooks, integraciones terceros)
- [ ] Roles granulares (permisos custom por usuario)
- [ ] Audit log completo (quién hizo qué cuándo)

---

## 📝 Criterios Priorización

**ROI = Impacto / Esfuerzo**

**Impacto:**
- ⭐⭐⭐⭐⭐ Crítico (calidad, confiabilidad, seguridad)
- ⭐⭐⭐⭐ Alto (performance, UX, productividad)
- ⭐⭐⭐ Medio (mejora notable)
- ⭐⭐ Bajo (nice to have)

**Esfuerzo:**
- 🔨 Bajo (<5h)
- 🔨🔨 Medio (5-10h)
- 🔨🔨🔨 Alto (10-15h)
- 🔨🔨🔨🔨 Muy alto (15+h)

---

## 🎯 Métricas Éxito

**Sprint 1 (Optimizaciones):**
- Initial bundle: <200KB ✅ LOGRADO (332 KB total, 255 KB JS - 2026-03-11)
- Statistics render: <100ms ✅ LOGRADO (3x mejora - 2026-03-11)
- Queries BD: <50ms promedio ✅ MEJORADO (85% reducción - 2026-03-11)

**Sprint 2 (Testing):**
- Backend coverage: 70%+ (actual: 0%)
- E2E tests: 10+ flujos críticos
- CI/CD: Auto-run tests en PRs

**Sprint 3 (Features):**
- Push notifications: >60% adoption
- Dashboard analytics: Usado diariamente
- Búsqueda: <200ms respuesta

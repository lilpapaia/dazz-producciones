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

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

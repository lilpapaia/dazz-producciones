# 🚀 INSTALACIÓN DE MEJORAS - Dazz Producciones

**Fecha:** 04 Marzo 2026  
**Archivos Entregados:** 4

---

## 📦 ARCHIVOS INCLUIDOS

1. **DOCUMENTACION_COMPLETA.md** - Documentación técnica completa
2. **claude_ai_MEJORADO.py** - Detección fechas multiidioma
3. **ReviewTicket_MEJORADO.jsx** - Lightbox para ver imágenes
4. **INSTRUCCIONES_INSTALACION.md** - Este archivo

---

## 🔧 MEJORA 1: Detección Fechas Multiidioma

### Problema Solucionado
La IA no detectaba fechas en catalán u otros idiomas:
- "17 de desembre de 2025" → No convertía
- "December 17, 2025" → No convertía

### Solución Implementada
Prompt mejorado que detecta fechas en:
- **Catalán:** desembre, gener, març, etc.
- **Español:** diciembre, enero, marzo, etc.
- **Inglés:** December, January, March, etc.
- **Italiano:** dicembre, gennaio, marzo, etc.
- **Francés:** décembre, janvier, mars, etc.
- **Portugués:** dezembro, janeiro, março, etc.

**Siempre convierte a:** DD/MM/YYYY

### Instalación

**Ubicación:** `backend/app/services/claude_ai.py`

**Pasos:**
```bash
cd C:\Users\lilpa\OneDrive\Escritorio\dazz-producciones\backend\app\services

# Hacer backup del archivo actual
copy claude_ai.py claude_ai_backup.py

# Reemplazar con el archivo mejorado
# (copiar claude_ai_MEJORADO.py y renombrar a claude_ai.py)
```

**Alternativa CMD:**
```bash
cd backend\app\services
ren claude_ai.py claude_ai_backup.py
copy C:\Downloads\claude_ai_MEJORADO.py claude_ai.py
```

**Reiniciar backend:**
```bash
# Detener servidor (Ctrl+C)
python main.py
```

### Verificación
1. Sube la factura catalana de prueba (17 de desembre de 2025)
2. Verifica que la fecha se convierte a "17/12/2025"
3. Prueba con fechas en inglés, italiano, etc.

---

## 🖼️ MEJORA 2: Lightbox para Ver Imágenes

### Problema Solucionado
No había forma de ver la imagen del ticket escaneado:
- Solo placeholder con icono ojo
- No se podía verificar visualmente el ticket

### Solución Implementada
- **Miniatura** del ticket escaneado (altura 256px)
- **Hover effect** con icono zoom
- **Click** → Modal lightbox pantalla completa
- **Botón X** para cerrar
- **Click fuera** del modal para cerrar
- **Fondo blur** semi-transparente

### Instalación

**Ubicación:** `frontend/src/pages/ReviewTicket.jsx`

**Pasos:**
```bash
cd C:\Users\lilpa\OneDrive\Escritorio\dazz-producciones\frontend\src\pages

# Hacer backup del archivo actual
copy ReviewTicket.jsx ReviewTicket_backup.jsx

# Reemplazar con el archivo mejorado
# (copiar ReviewTicket_MEJORADO.jsx y renombrar a ReviewTicket.jsx)
```

**Alternativa CMD:**
```bash
cd frontend\src\pages
ren ReviewTicket.jsx ReviewTicket_backup.jsx
copy C:\Downloads\ReviewTicket_MEJORADO.jsx ReviewTicket.jsx
```

**Reiniciar frontend:**
```bash
# Detener servidor (Ctrl+C)
cd frontend
npm run dev
```

### Verificación
1. Abre un proyecto con tickets
2. Click en un ticket → ReviewTicket
3. Verifica que se muestra miniatura de la imagen
4. Hover sobre imagen → aparece icono zoom
5. Click imagen → modal pantalla completa
6. Click X o fuera → cierra modal

---

## 📋 MEJORA 3: Campo Notes en Base de Datos

### Problema Solucionado
Faltaba campo "notes" en la tabla tickets para guardar notas adicionales (PO si aplica)

### Solución Implementada
Script `update_db.py` que añade columna `notes TEXT` a la tabla tickets

### Instalación

**Ya debería estar ejecutado**, pero si no:

```bash
cd C:\Users\lilpa\OneDrive\Escritorio\dazz-producciones\backend
python update_db.py
```

**Deberías ver:**
```
🔧 Actualizando base de datos...
  ✓ notes ya existe
✅ Base de datos actualizada correctamente
```

---

## ✅ CHECKLIST COMPLETO

### Backend:
- [ ] Backup de `claude_ai.py` creado
- [ ] `claude_ai_MEJORADO.py` copiado y renombrado
- [ ] Backend reiniciado
- [ ] Prueba con factura catalana → fecha convertida correctamente

### Frontend:
- [ ] Backup de `ReviewTicket.jsx` creado
- [ ] `ReviewTicket_MEJORADO.jsx` copiado y renombrado
- [ ] Frontend reiniciado
- [ ] Miniatura de imagen se muestra correctamente
- [ ] Lightbox funciona (click → modal → cerrar)

### Base de Datos:
- [ ] `update_db.py` ejecutado
- [ ] Campo `notes` existe en tabla tickets
- [ ] Campo notes se guarda y muestra en ReviewTicket

---

## 🔍 TROUBLESHOOTING

### Error: Imagen no carga en lightbox
**Problema:** URL incorrecta o archivo no existe
**Solución:**
1. Verificar que `file_path` en DB es correcto
2. Verificar que archivo existe en `backend/uploads/`
3. Verificar que backend sirve archivos estáticos:
   ```python
   # En main.py
   app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
   ```

### Error: Fecha sigue sin convertirse
**Problema:** Idioma no reconocido o formato extraño
**Solución:**
1. Verificar que `claude_ai.py` fue reemplazado correctamente
2. Revisar logs del backend para ver respuesta IA
3. Si es un idioma nuevo, añadir a la lista en el prompt

### Error: Campo notes no se guarda
**Problema:** Columna no existe en DB
**Solución:**
```bash
python update_db.py
```

---

## 📊 MEJORAS ADICIONALES SUGERIDAS

### Prioridad Alta (1 semana)

**1. Optimizar Velocidad IA**
- Cache de respuestas IA para imágenes similares
- Reducir tokens del prompt (actualmente ~800 tokens)
- Usar Claude Haiku para tickets simples (más rápido y barato)

**2. Validación de Datos IA**
- Verificar que fecha sea válida (no futura)
- Verificar que importes sean > 0
- Detectar IVA incorrecto (21% vs 10% vs 4%)
- Alert usuario si confidence < 0.7

**3. Mejoras UI/UX**
- Drag & drop para reordenar tickets
- Edición inline en lista (sin ir a ReviewTicket)
- Teclado shortcuts (Ctrl+S guardar, Esc cerrar)
- Búsqueda tickets por proveedor/fecha

### Prioridad Media (1 mes)

**4. Exportar Múltiples Formatos**
- PDF además de Excel
- CSV para importar en otras herramientas
- Envío automático a email adicionales

**5. Dashboard con Estadísticas**
- Gráficas por mes (recharts)
- Top proveedores
- Estado facturas (pendientes vs recibidas)
- Alertas pagos atrasados

**6. Multi-idioma Frontend**
- i18n con react-i18next
- Español/Catalán/Inglés
- Detectar idioma navegador

### Prioridad Baja (3+ meses)

**7. App Móvil React Native**
- Escanear con cámara
- Notificaciones push
- Modo offline

**8. Integración Contabilidad**
- Export a Contaplus, A3, Sage
- API para ERP
- Sincronización bidireccional

---

## 📞 SOPORTE

Si tienes problemas con la instalación:
1. Verifica que los archivos backup existen
2. Lee la sección Troubleshooting
3. Revisa logs del backend: `tail -f backend.log`
4. Verifica consola del navegador (F12) para errores frontend

---

## 🎯 PRÓXIMOS PASOS

1. **HOY:** Instalar mejoras 1 y 2
2. **Esta semana:** Probar con facturas reales
3. **Siguiente semana:** Decidir próximas mejoras del roadmap

---

**¡Listo para usar!** 🚀

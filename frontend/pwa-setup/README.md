# 📱 PWA DAZZ PRODUCCIONES - ARCHIVOS COMPLETOS

## 📦 Contenido de esta Carpeta

### 📄 **Documentación**
- `GUIA_INSTALACION_PWA.md` - Guía paso a paso completa
- `README.md` - Este archivo (resumen rápido)

### 🔧 **Scripts de Setup**
- `setup-pwa.sh` - Script automatizado (bash)
- `generate-icons.js` - Genera todos los tamaños de iconos

### ⚙️ **Configuración**
- `vite.config.js` - Configuración Vite + vite-plugin-pwa
- `manifest.json` - Referencia del manifiesto PWA
- `service-worker.js` - Referencia del service worker

### ⚛️ **Componentes React**
- `PWAComponents.jsx` - Componentes de actualización e instalación

### 🎨 **Assets**
- `icon-512x512.png` - Icono base (todos los demás se generan desde este)

---

## ⚡ INSTALACIÓN RÁPIDA

```bash
# 1. Ir a frontend/
cd frontend

# 2. Copiar TODOS los archivos de pwa-setup/ a frontend/

# 3. Ejecutar script automatizado
bash setup-pwa.sh

# 4. Seguir instrucciones en pantalla
```

---

## 📖 QUÉ HACE CADA ARCHIVO

### **generate-icons.js**
Genera 8 tamaños de iconos (72, 96, 128, 144, 152, 192, 384, 512) desde `icon-512x512.png`

**Uso:**
```bash
node generate-icons.js
```

**Output:** `public/icons/icon-{tamaño}.png`

---

### **vite.config.js**
Configuración Vite con vite-plugin-pwa que:
- ✅ Genera manifest.json automático
- ✅ Registra service worker
- ✅ Configura estrategias de cache
- ✅ Habilita PWA en desarrollo

**Reemplaza:** Tu vite.config.js actual (hace backup automático)

---

### **PWAComponents.jsx**
3 componentes React:

**1. `<PWAUpdatePrompt />`**
Toast que aparece cuando hay actualización disponible

**2. `<PWAInstallPrompt />`**
Banner que invita a instalar la app

**3. `useIsPWA()`**
Hook para detectar si está instalada como PWA

**Uso:**
```jsx
// App.jsx
import { PWAUpdatePrompt, PWAInstallPrompt } from './components/PWAComponents';

function App() {
  return (
    <>
      {/* Tu app */}
      <PWAUpdatePrompt />
      <PWAInstallPrompt />
    </>
  );
}
```

---

### **setup-pwa.sh**
Script automatizado que:
1. Instala dependencias (`vite-plugin-pwa`, `sharp`)
2. Crea carpetas necesarias
3. Genera iconos
4. Hace backup de archivos existentes
5. Te dice qué pasos manuales faltan

**Uso:**
```bash
bash setup-pwa.sh
```

---

## ✅ RESULTADO FINAL

**Desktop:**
- Icono "DAZZ Producciones" en escritorio
- Ventana propia sin barra navegador
- Funciona offline
- Actualizaciones automáticas

**Mobile:**
- Icono en home screen
- App fullscreen
- Indistinguible de app nativa

---

## 🎯 PASOS MANUALES

Después de ejecutar `setup-pwa.sh`:

1. **Reemplazar vite.config.js**
2. **Actualizar App.jsx** (añadir componentes PWA)
3. **Actualizar index.html** (añadir meta tags)
4. **Build:** `npm run build`
5. **Test:** `npm run preview`
6. **Deploy:** `git push`

Todo explicado en **GUIA_INSTALACION_PWA.md**

---

## 📊 ESTRUCTURA FINAL

```
frontend/
├── public/
│   └── icons/
│       ├── icon-72x72.png
│       ├── icon-96x96.png
│       ├── icon-128x128.png
│       ├── icon-144x144.png
│       ├── icon-152x152.png
│       ├── icon-192x192.png
│       ├── icon-384x384.png
│       └── icon-512x512.png
├── src/
│   ├── components/
│   │   └── PWAComponents.jsx
│   ├── App.jsx (modificado)
│   └── main.jsx
├── vite.config.js (reemplazado)
├── index.html (modificado)
└── generate-icons.js
```

---

## 🐛 TROUBLESHOOTING

Ver sección completa en `GUIA_INSTALACION_PWA.md`

**Problemas comunes:**
- Iconos no aparecen → `node generate-icons.js`
- No se registra SW → Hard refresh (Ctrl+Shift+R)
- No aparece "Instalar" → Verificar HTTPS + manifest válido

---

**Tiempo estimado:** 1-2 horas
**Dificultad:** Media
**Compatibilidad:** 100% (todos los navegadores y móviles)

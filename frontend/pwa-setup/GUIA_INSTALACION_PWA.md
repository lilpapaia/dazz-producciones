# 📱 GUÍA COMPLETA - PWA DAZZ PRODUCCIONES

## 🎯 Qué es PWA

**Progressive Web App** = App web que se puede instalar como app nativa

**Resultado final:**
- ✅ Icono en escritorio/dock
- ✅ Se abre en ventana propia (sin barra navegador)
- ✅ Funciona offline
- ✅ Actualizaciones automáticas
- ✅ Notificaciones (opcional)
- ✅ Acceso rápido con shortcuts

---

## 📦 INSTALACIÓN COMPLETA

### **1. Instalar dependencias**

```bash
cd frontend

# Instalar vite-plugin-pwa
npm install -D vite-plugin-pwa

# Instalar workbox (incluido automáticamente)
# Instalar sharp para generar iconos
npm install -D sharp
```

---

### **2. Generar iconos**

```bash
# Copiar icon-512x512.png a raíz de frontend/
cp /ruta/icon-512x512.png ./

# Copiar script de generación
cp generate-icons.js ./

# Ejecutar generación de iconos
node generate-icons.js
```

**Output esperado:**
```
✅ 72x72 → public/icons/icon-72x72.png
✅ 96x96 → public/icons/icon-96x96.png
✅ 128x128 → public/icons/icon-128x128.png
✅ 144x144 → public/icons/icon-144x144.png
✅ 152x152 → public/icons/icon-152x152.png
✅ 192x192 → public/icons/icon-192x192.png
✅ 384x384 → public/icons/icon-384x384.png
✅ 512x512 → public/icons/icon-512x512.png
```

---

### **3. Reemplazar vite.config.js**

```bash
# Backup del actual
cp vite.config.js vite.config.js.backup

# Copiar nuevo config con PWA
cp vite.config.js ./
```

---

### **4. Crear componentes PWA**

```bash
# Crear carpeta de componentes si no existe
mkdir -p src/components

# Copiar componentes PWA
cp PWAComponents.jsx src/components/
```

---

### **5. Actualizar App.jsx**

Añadir los componentes PWA al layout principal:

```jsx
// src/App.jsx
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { PWAUpdatePrompt, PWAInstallPrompt } from './components/PWAComponents';

// ... tus imports existentes

function App() {
  return (
    <AuthProvider>
      <Router>
        {/* Tus rutas existentes */}
        <Routes>
          {/* ... */}
        </Routes>
        
        {/* Componentes PWA - AÑADIR AQUÍ */}
        <PWAUpdatePrompt />
        <PWAInstallPrompt />
      </Router>
    </AuthProvider>
  );
}

export default App;
```

---

### **6. Actualizar index.html**

Añadir meta tags para PWA:

```html
<!-- frontend/index.html -->
<!doctype html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    
    <!-- PWA Meta Tags - AÑADIR AQUÍ -->
    <meta name="theme-color" content="#f59e0b" />
    <meta name="description" content="Gestión de tickets y proyectos creativos para DAZZ Creative" />
    <meta name="apple-mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
    <meta name="apple-mobile-web-app-title" content="DAZZ" />
    
    <!-- Apple Touch Icons -->
    <link rel="apple-touch-icon" sizes="192x192" href="/icons/icon-192x192.png" />
    <link rel="apple-touch-icon" sizes="512x512" href="/icons/icon-512x512.png" />
    
    <!-- Favicon existente -->
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    
    <title>DAZZ Producciones</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

---

### **7. Build y test**

```bash
# Build de producción
npm run build

# Preview local
npm run preview

# Debería mostrar:
# ✅ PWA ready to work offline
```

---

### **8. Deploy a Vercel**

```bash
git add .
git commit -m "feat: PWA completa - app instalable"
git push origin main
```

Vercel despliega automáticamente (~1 min)

---

## ✅ TESTING

### **Desktop (Chrome/Edge):**

1. Ir a `https://producciones.dazzcreative.com`
2. En barra de direcciones aparece: **⬇️ Instalar**
3. Click → "Instalar DAZZ Producciones"
4. App instalada en escritorio

**O desde menú:**
- Chrome: Menu → Más herramientas → Crear acceso directo → ✓ Abrir como ventana
- Edge: Menu → Apps → Instalar este sitio como app

### **Mobile (iOS):**

1. Safari → `https://producciones.dazzcreative.com`
2. Tap botón compartir (⬆️)
3. "Añadir a pantalla de inicio"
4. Icono DAZZ aparece en home screen

### **Mobile (Android):**

1. Chrome → `https://producciones.dazzcreative.com`
2. Popup: "Añadir DAZZ Producciones a la pantalla de inicio"
3. Tap "Añadir"
4. Icono DAZZ aparece en launcher

---

## 🎨 PERSONALIZACIÓN

### **Cambiar colores:**

```js
// vite.config.js
manifest: {
  theme_color: '#f59e0b',        // Color de la barra superior (amber)
  background_color: '#09090b'    // Color de fondo al cargar (zinc-950)
}
```

### **Añadir shortcuts:**

```js
// vite.config.js
shortcuts: [
  {
    name: 'Nuevo Proyecto',
    url: '/projects/create',
    icons: [{ src: '/icons/icon-96x96.png', sizes: '96x96' }]
  },
  {
    name: 'Subir Ticket',
    url: '/projects',
    icons: [{ src: '/icons/icon-96x96.png', sizes: '96x96' }]
  }
]
```

### **Estrategia de cache:**

Editar en `vite.config.js` → `workbox.runtimeCaching`

**Opciones:**
- `NetworkFirst`: Intenta red, fallback cache (para API)
- `CacheFirst`: Usa cache, fallback red (para imágenes)
- `StaleWhileRevalidate`: Usa cache pero actualiza en background

---

## 🐛 TROUBLESHOOTING

### **Problema: Iconos no aparecen**

```bash
# Verificar que existen
ls -la public/icons/

# Regenerar si faltan
node generate-icons.js
```

### **Problema: Service Worker no se registra**

```bash
# Verificar en consola navegador (F12):
# Debería mostrar: "✅ Service Worker registrado"

# Limpiar cache:
# DevTools → Application → Clear storage → Clear site data
```

### **Problema: No aparece botón "Instalar"**

**Requisitos para PWA:**
- ✅ HTTPS (Vercel lo hace automático)
- ✅ manifest.json válido
- ✅ Service Worker registrado
- ✅ Iconos 192x192 y 512x512

**Verificar:**
```
Chrome DevTools → Application → Manifest
Chrome DevTools → Application → Service Workers
```

### **Problema: Cambios no se ven después de deploy**

```bash
# Hard refresh en navegador:
Ctrl + Shift + R (Windows/Linux)
Cmd + Shift + R (Mac)

# O limpiar cache:
DevTools → Application → Clear storage
```

---

## 📊 ARCHIVOS FINALES

```
frontend/
├── public/
│   ├── icons/
│   │   ├── icon-72x72.png
│   │   ├── icon-96x96.png
│   │   ├── icon-128x128.png
│   │   ├── icon-144x144.png
│   │   ├── icon-152x152.png
│   │   ├── icon-192x192.png
│   │   ├── icon-384x384.png
│   │   └── icon-512x512.png
│   └── favicon.svg
├── src/
│   ├── components/
│   │   └── PWAComponents.jsx  ← NUEVO
│   ├── App.jsx  ← MODIFICADO (añadir PWA components)
│   └── main.jsx
├── index.html  ← MODIFICADO (meta tags PWA)
├── vite.config.js  ← REEMPLAZADO (con vite-plugin-pwa)
├── icon-512x512.png  ← BASE para generar iconos
└── generate-icons.js  ← Script generación
```

---

## 🎯 RESULTADO FINAL

**Desktop:**
- Icono "DAZZ Producciones" en escritorio
- Doble click → Abre en ventana propia
- Sin barra de navegador
- Funciona offline

**Mobile:**
- Icono en home screen
- Tap → Abre fullscreen
- Indistinguible de app nativa

**Actualizaciones:**
- Automáticas (como web)
- Toast notification: "Nueva versión disponible"
- Click "Recargar" → Actualiza

---

## 📈 PRÓXIMOS PASOS (OPCIONAL)

### **Notificaciones Push:**
Editar `service-worker.js` para activar notificaciones

### **Offline completo:**
Guardar datos en IndexedDB cuando no hay red

### **Background Sync:**
Subir tickets cuando vuelva la conexión

---

**Estado:** ✅ LISTO PARA IMPLEMENTAR
**Tiempo total:** ~2 horas
**Compatibilidad:** Chrome, Edge, Safari, Firefox, todos móviles

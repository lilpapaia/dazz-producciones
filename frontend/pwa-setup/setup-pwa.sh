#!/bin/bash

# Script automatizado para instalar PWA en DAZZ Producciones
# Uso: bash setup-pwa.sh

set -e  # Exit on error

echo "🚀 Instalando PWA para DAZZ Producciones..."
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Verificar que estamos en frontend
if [ ! -f "package.json" ]; then
    echo "❌ Error: Ejecuta este script desde la carpeta frontend/"
    exit 1
fi

echo "${YELLOW}📦 Paso 1/6: Instalando dependencias...${NC}"
npm install -D vite-plugin-pwa sharp
echo "${GREEN}✅ Dependencias instaladas${NC}"
echo ""

# 2. Crear carpeta de iconos
echo "${YELLOW}📁 Paso 2/6: Creando estructura de carpetas...${NC}"
mkdir -p public/icons
echo "${GREEN}✅ Carpeta public/icons/ creada${NC}"
echo ""

# 3. Generar iconos (asumiendo que icon-512x512.png está en raíz)
echo "${YELLOW}🎨 Paso 3/6: Generando iconos...${NC}"
if [ -f "icon-512x512.png" ]; then
    node generate-icons.js
    echo "${GREEN}✅ Iconos generados en public/icons/${NC}"
else
    echo "${YELLOW}⚠️  icon-512x512.png no encontrado. Cópialo y ejecuta: node generate-icons.js${NC}"
fi
echo ""

# 4. Backup de vite.config.js
echo "${YELLOW}💾 Paso 4/6: Haciendo backup de vite.config.js...${NC}"
if [ -f "vite.config.js" ]; then
    cp vite.config.js vite.config.js.backup
    echo "${GREEN}✅ Backup guardado: vite.config.js.backup${NC}"
fi
echo ""

# 5. Crear componentes PWA
echo "${YELLOW}⚛️  Paso 5/6: Creando componentes React...${NC}"
mkdir -p src/components
# Asumiendo que PWAComponents.jsx está disponible
if [ -f "PWAComponents.jsx" ]; then
    cp PWAComponents.jsx src/components/
    echo "${GREEN}✅ Componentes PWA creados${NC}"
else
    echo "${YELLOW}⚠️  PWAComponents.jsx no encontrado${NC}"
fi
echo ""

# 6. Mostrar siguiente pasos
echo "${YELLOW}📝 Paso 6/6: Configuración manual necesaria${NC}"
echo ""
echo "Sigue estos pasos:"
echo ""
echo "1️⃣  Reemplazar vite.config.js con el nuevo (ya tienes backup)"
echo "2️⃣  Actualizar App.jsx para incluir PWA components:"
echo "    import { PWAUpdatePrompt, PWAInstallPrompt } from './components/PWAComponents';"
echo "    // Al final del return:"
echo "    <PWAUpdatePrompt />"
echo "    <PWAInstallPrompt />"
echo ""
echo "3️⃣  Actualizar index.html con meta tags PWA (ver guía)"
echo ""
echo "4️⃣  Build y test:"
echo "    npm run build"
echo "    npm run preview"
echo ""
echo "5️⃣  Deploy a Vercel:"
echo "    git add ."
echo "    git commit -m 'feat: PWA completa'"
echo "    git push origin main"
echo ""
echo "${GREEN}✨ Setup completado! Consulta GUIA_INSTALACION_PWA.md para más detalles${NC}"

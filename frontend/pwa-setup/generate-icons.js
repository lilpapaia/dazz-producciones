#!/usr/bin/env node

/**
 * Script para generar todos los tamaños de iconos PWA desde icon-512x512.png
 * 
 * Requiere: npm install sharp --save-dev
 * Uso: node generate-icons.js
 */

const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const sizes = [72, 96, 128, 144, 152, 192, 384, 512];
const inputFile = 'icon-512x512.png';
const outputDir = 'public/icons';

// Crear directorio de output si no existe
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
  console.log(`✅ Directorio creado: ${outputDir}`);
}

// Generar iconos
console.log('🎨 Generando iconos PWA...\n');

Promise.all(
  sizes.map(size => {
    const outputFile = path.join(outputDir, `icon-${size}x${size}.png`);
    
    return sharp(inputFile)
      .resize(size, size, {
        fit: 'contain',
        background: { r: 0, g: 0, b: 0, alpha: 0 }
      })
      .png()
      .toFile(outputFile)
      .then(() => {
        console.log(`✅ ${size}x${size} → ${outputFile}`);
      })
      .catch(err => {
        console.error(`❌ Error generando ${size}x${size}:`, err.message);
      });
  })
).then(() => {
  console.log('\n🎉 ¡Todos los iconos generados correctamente!');
  console.log(`📁 Ubicación: ${outputDir}/`);
}).catch(err => {
  console.error('❌ Error general:', err);
  process.exit(1);
});

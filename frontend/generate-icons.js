import sharp from 'sharp';
import fs from 'fs';
import path from 'path';

const sizes = [72, 96, 128, 144, 152, 192, 384, 512];
const inputFile = 'icon-512x512.png';
const outputDir = 'public/icons';

if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
  console.log(`? Directorio creado: ${outputDir}`);
}

console.log('?? Generando iconos PWA...\\n');

Promise.all(
  sizes.map(size => {
    const outputFile = path.join(outputDir, `icon-${size}x${size}.png`);
    return sharp(inputFile)
      .resize(size, size, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
      .png()
      .toFile(outputFile)
      .then(() => console.log(`? ${size}x${size}  ${outputFile}`))
      .catch(err => console.error(`? Error ${size}x${size}:`, err.message));
  })
).then(() => {
  console.log('\\n?? ­Todos los iconos generados correctamente!');
}).catch(err => {
  console.error('? Error:', err);
  process.exit(1);
});

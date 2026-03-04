#!/bin/bash

echo "🚀 DAZZ CREATIVE - Sistema Gestión Gastos"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
    echo "✅ Entorno virtual creado"
fi

# Activate virtual environment
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Install dependencies
echo "📥 Instalando dependencias..."
pip install -r requirements.txt --quiet

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Archivo .env no encontrado"
    echo "📝 Copiando .env.example a .env..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANTE: Edita el archivo .env y añade tu ANTHROPIC_API_KEY"
    echo "   Obtén tu API key en: https://console.anthropic.com"
    echo ""
    read -p "Presiona ENTER cuando hayas configurado .env..."
fi

# Create uploads directory
mkdir -p uploads

echo ""
echo "✅ Todo listo!"
echo ""
echo "🌐 Iniciando servidor en http://localhost:8000"
echo "📚 Documentación: http://localhost:8000/docs"
echo ""
echo "-------------------------------------------"
echo "Presiona Ctrl+C para detener el servidor"
echo "-------------------------------------------"
echo ""

# Start server
python main.py

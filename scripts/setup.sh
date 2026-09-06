#!/bin/bash
set -e

echo "🚀 Configurando Sistema de Facturación Electrónica"

if ! command -v uv &> /dev/null; then
    echo "❌ uv no está instalado. Instalando..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

echo "📦 Instalando dependencias..."
make dev

echo "🔧 Configurando pre-commit..."
uv run pre-commit install

if [ ! -f .env ]; then
    echo "📝 Creando archivo .env"
    cp .env.example .env
    echo "⚠️  Edita .env con tus credenciales"
fi

echo "🗄️  Ejecutando migraciones..."
make migrate

echo "👤 Creando superusuario..."
make superuser

echo ""
echo "✅ Configuración completada!"
echo "🚀 Ejecuta: make run"
#!/bin/bash
# Script para validar los XML generados

echo "🔍 Validando XML contra XSD del SII"
echo "=================================="

# Verificar que existen los XML
if [ ! -f "../libro_diario.xml" ] && [ ! -f "../libro_mayor.xml" ] && [ ! -f "../diccionario.xml" ]; then
    echo "⚠️  No se encontraron archivos XML en el directorio raíz."
    echo "Primero descarga los XML desde el sistema:"
    echo "  curl -u admin:admin http://localhost:8000/lce/libro-diario/?año=2026&mes=8 -o ../libro_diario.xml"
    echo "  curl -u admin:admin http://localhost:8000/lce/libro-mayor/?año=2026&mes=8 -o ../libro_mayor.xml"
    echo "  curl -u admin:admin http://localhost:8000/lce/diccionario/?año=2026 -o ../diccionario.xml"
    exit 1
fi

# Copiar XML al directorio de validación
echo "📂 Copiando archivos XML..."
cp ../libro_diario.xml xml_samples/ 2>/dev/null || echo "  libro_diario.xml no encontrado"
cp ../libro_mayor.xml xml_samples/ 2>/dev/null || echo "  libro_mayor.xml no encontrado"
cp ../diccionario.xml xml_samples/ 2>/dev/null || echo "  diccionario.xml no encontrado"

# Ejecutar validación
echo "🚀 Ejecutando validación..."
uv run python validate_xsd.py

# Mostrar resultado
echo ""
echo "📄 Reporte generado en: reports/validacion_report.json"

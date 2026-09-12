#!/usr/bin/env python
"""
Validador específico para Libro Diario
"""

import sys

import xmlschema


def validate_diario(xml_file, xsd_file="schemas/sii/LceDiario_v10.xsd"):
    """Valida un archivo XML de Libro Diario"""
    try:
        schema = xmlschema.XMLSchema(xsd_file)
        schema.validate(xml_file)
        print(f"✅ {xml_file} es VÁLIDO")
        return True
    except Exception as e:
        print(f"❌ {xml_file} es INVÁLIDO")
        print(f"   Error: {str(e)[:200]}...")
        return False


if __name__ == "__main__":
    xml_file = "xml_samples/libro_diario.xml"
    if len(sys.argv) > 1:
        xml_file = sys.argv[1]
    validate_diario(xml_file)

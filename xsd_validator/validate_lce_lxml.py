#!/usr/bin/env python
"""
Validador de LCE usando lxml con manejo de namespaces
"""

import os
from pathlib import Path

from lxml import etree


def validate_with_lxml(xml_file, xsd_file, namespace="http://www.sii.cl/SiiLce"):
    """Valida un XML contra un XSD usando lxml"""
    try:
        # Cargar el esquema
        with open(xsd_file, "rb") as f:
            schema_root = etree.XML(f.read())

        # Crear el validador
        schema = etree.XMLSchema(schema_root)

        # Cargar el XML
        with open(xml_file, "rb") as f:
            xml_content = f.read()

        # Parsear el XML con el namespace
        parser = etree.XMLParser()
        doc = etree.fromstring(xml_content, parser)

        # Validar
        schema.assertValid(doc)
        print(f"✅ {Path(xml_file).name} es VÁLIDO")
        return True

    except etree.DocumentInvalid as e:
        print(f"❌ {Path(xml_file).name} es INVÁLIDO")
        print(f"   Error: {e}")
        return False
    except etree.XMLSchemaParseError as e:
        print(f"❌ Error en el esquema: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Función principal"""
    files = [
        ("xml_samples/libro_diario.xml", "schemas/sii/LceDiario_v10.xsd"),
        ("xml_samples/libro_mayor.xml", "schemas/sii/LceMayor_v10.xsd"),
        ("xml_samples/diccionario.xml", "schemas/sii/LceDic_v10.xsd"),
    ]

    print("🔍 Validando XML contra XSD de LCE")
    print("=" * 60)

    results = []
    for xml_file, xsd_file in files:
        if not os.path.exists(xml_file):
            print(f"⚠️  {xml_file} no encontrado")
            continue
        if not os.path.exists(xsd_file):
            print(f"⚠️  {xsd_file} no encontrado")
            continue

        valid = validate_with_lxml(xml_file, xsd_file)
        results.append({"file": xml_file, "valid": valid})

    # Resumen
    valid_count = sum(1 for r in results if r["valid"])
    total = len(results)
    print("\n" + "=" * 60)
    print(f"📊 Resumen: {valid_count}/{total} válidos")


if __name__ == "__main__":
    main()

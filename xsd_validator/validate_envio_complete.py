#!/usr/bin/env python
"""
Validador de LCE usando el XSD de envío de libros
"""

import os
from pathlib import Path

from lxml import etree


def load_schema(xsd_file):
    """Carga un XSD con las inclusiones correctas"""
    with open(xsd_file, encoding="latin-1") as f:
        content = f.read()

    # Reemplazar inclusiones con rutas absolutas
    include_dir = str(Path(xsd_file).parent.absolute())
    replacements = [
        ("LceSiiTypes_v10.xsd", "LceSiiTypes_v10.xsd"),
        ("LceDiarioRes_v10.xsd", "LceDiarioRes_v10.xsd"),
        ("LceMayorRes_v10.xsd", "LceMayorRes_v10.xsd"),
        ("LceBalance_v10.xsd", "LceBalance_v10.xsd"),
        ("LceDic_v10.xsd", "LceDic_v10.xsd"),
        ("LceCal_v10.xsd", "LceCal_v10.xsd"),
        ("LceCoCertif_v10.xsd", "LceCoCertif_v10.xsd"),
        ("LceCoCierre_v10.xsd", "LceCoCierre_v10.xsd"),
        ("LceMayor_v10.xsd", "LceMayor_v10.xsd"),
        ("LceDiario_v10.xsd", "LceDiario_v10.xsd"),
        ("LceResultado_v10.xsd", "LceResultado_v10.xsd"),
        ("xmldsignature_v10.xsd", "xmldsignature_v10.xsd"),
    ]

    for original, filename in replacements:
        content = content.replace(f'schemaLocation="{original}"', f'schemaLocation="{include_dir}/{filename}"')

    return etree.XMLSchema(etree.XML(content.encode("utf-8")))


def validate_file(xml_file):
    """Valida un archivo XML usando el XSD de envío"""
    try:
        # Cargar el XML
        with open(xml_file, "rb") as f:
            xml_content = f.read()
        doc = etree.fromstring(xml_content)

        print(f"\n📄 {Path(xml_file).name}")

        # Intentar validar como parte de un envío
        xsd_file = "schemas/sii/LceEnvioLibros_v10.xsd"
        if not os.path.exists(xsd_file):
            print(f"  ⚠️  XSD no encontrado: {xsd_file}")
            return False

        schema = load_schema(xsd_file)
        schema.assertValid(doc)
        print("  ✅ VÁLIDO (como envío de libros)")
        return True

    except etree.DocumentInvalid as e:
        print(f"  ❌ INVÁLIDO: {e}")
        return False
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return False


def validate_with_libro_xsd(xml_file, xsd_type):
    """Valida un XML usando su propio XSD de libro"""
    try:
        # Cargar el XML
        with open(xml_file, "rb") as f:
            xml_content = f.read()

        print(f"\n📄 {Path(xml_file).name}")

        # Usar el XSD correspondiente
        xsd_map = {
            "diario": "schemas/sii/LceDiario_v10.xsd",
            "mayor": "schemas/sii/LceMayor_v10.xsd",
            "diccionario": "schemas/sii/LceDic_v10.xsd",
        }

        xsd_file = xsd_map.get(xsd_type)
        if not xsd_file or not os.path.exists(xsd_file):
            print(f"  ⚠️  XSD no encontrado: {xsd_file}")
            return False

        # Cargar el XSD
        with open(xsd_file, encoding="latin-1") as f:
            xsd_content = f.read()

        # Reemplazar inclusiones
        include_dir = str(Path(xsd_file).parent.absolute())
        xsd_content = xsd_content.replace(
            'schemaLocation="LceSiiTypes_v10.xsd"', f'schemaLocation="{include_dir}/LceSiiTypes_v10.xsd"'
        )
        xsd_content = xsd_content.replace(
            'schemaLocation="LceDiarioRes_v10.xsd"', f'schemaLocation="{include_dir}/LceDiarioRes_v10.xsd"'
        )
        xsd_content = xsd_content.replace(
            'schemaLocation="xmldsignature_v10.xsd"', f'schemaLocation="{include_dir}/xmldsignature_v10.xsd"'
        )

        schema = etree.XMLSchema(etree.XML(xsd_content.encode("utf-8")))

        # Intentar validar
        doc = etree.fromstring(xml_content)
        schema.assertValid(doc)
        print("  ✅ VÁLIDO")
        return True

    except etree.DocumentInvalid as e:
        print(f"  ❌ INVÁLIDO: {e}")
        return False
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return False


def main():
    """Función principal"""
    print("🔍 Validando Libros Contables Electrónicos")
    print("=" * 60)

    files = {
        "diario": "xml_samples/libro_diario.xml",
        "mayor": "xml_samples/libro_mayor.xml",
        "diccionario": "xml_samples/diccionario.xml",
    }

    print("\n📍 Validando como archivos individuales...")
    for xsd_type, xml_file in files.items():
        if os.path.exists(xml_file):
            validate_with_libro_xsd(xml_file, xsd_type)
        else:
            print(f"\n⚠️  {xml_file} no encontrado")

    print("\n" + "=" * 60)
    print("✅ Validación completada")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
Corrige los XML agregando el namespace y valida
"""

import os
import re
from pathlib import Path

from lxml import etree


def fix_namespace(xml_file, namespace="http://www.sii.cl/SiiLce"):
    """Agrega el namespace al elemento raíz si no lo tiene"""
    with open(xml_file, encoding="utf-8") as f:
        content = f.read()

    # Verificar si ya tiene namespace
    if "xmlns" in content:
        return content

    # Agregar namespace al elemento raíz
    # Buscar el primer tag
    match = re.search(r"<([a-zA-Z0-9_]+)", content)
    if match:
        root_tag = match.group(1)
        # Reemplazar el tag por uno con namespace
        new_content = re.sub(f"<{root_tag}", f'<{root_tag} xmlns="{namespace}"', content, count=1)
        return new_content

    return content


def validate_with_namespace(xml_file, xsd_type="diario"):
    """Valida un XML con su XSD usando el namespace correcto"""
    try:
        print(f"\n📄 {Path(xml_file).name}")

        # Corregir el XML
        fixed_content = fix_namespace(xml_file)

        # Parsear el XML corregido
        doc = etree.fromstring(fixed_content.encode("utf-8"))

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

        # Reemplazar inclusiones con rutas absolutas
        include_dir = str(Path(xsd_file).parent.absolute())
        replacements = [
            ("LceSiiTypes_v10.xsd", "LceSiiTypes_v10.xsd"),
            ("LceDiarioRes_v10.xsd", "LceDiarioRes_v10.xsd"),
            ("LceMayorRes_v10.xsd", "LceMayorRes_v10.xsd"),
            ("xmldsignature_v10.xsd", "xmldsignature_v10.xsd"),
        ]

        for original, filename in replacements:
            xsd_content = xsd_content.replace(
                f'schemaLocation="{original}"', f'schemaLocation="{include_dir}/{filename}"'
            )

        schema = etree.XMLSchema(etree.XML(xsd_content.encode("utf-8")))

        # Validar
        schema.assertValid(doc)
        print("  ✅ VÁLIDO")

        # Guardar la versión corregida
        fixed_file = xml_file.replace(".xml", "_fixed.xml")
        with open(fixed_file, "w", encoding="utf-8") as f:
            f.write(fixed_content)
        print(f"  📝 Versión corregida guardada como: {fixed_file}")

        return True

    except etree.DocumentInvalid as e:
        print(f"  ❌ INVÁLIDO: {e}")
        return False
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return False


def main():
    """Función principal"""
    print("🔍 Corrigiendo y validando Libros Contables Electrónicos")
    print("=" * 60)

    files = {
        "diario": "xml_samples/libro_diario.xml",
        "mayor": "xml_samples/libro_mayor.xml",
        "diccionario": "xml_samples/diccionario.xml",
    }

    results = []
    for xsd_type, xml_file in files.items():
        if os.path.exists(xml_file):
            valid = validate_with_namespace(xml_file, xsd_type)
            results.append((xml_file, valid))
        else:
            print(f"\n⚠️  {xml_file} no encontrado")
            results.append((xml_file, False))

    print("\n" + "=" * 60)
    print("📊 Resumen:")
    for file, valid in results:
        status = "✅" if valid else "❌"
        print(f"  {status} {Path(file).name}")

    print("\n📝 Archivos corregidos guardados como *_fixed.xml")
    print("   Puedes usarlos para el envío al SII")


if __name__ == "__main__":
    main()

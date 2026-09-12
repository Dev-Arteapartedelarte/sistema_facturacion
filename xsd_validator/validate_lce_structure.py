#!/usr/bin/env python
"""
Validador de estructura LCE - Verifica que todos los elementos requeridos estén presentes,
excepto RutFirma y TmstFirma (que serán agregados por la capa Python)
"""

import os
from pathlib import Path

from lxml import etree


def validate_structure(xml_file):
    """Valida la estructura del XML sin verificar firma"""
    try:
        with open(xml_file, "rb") as f:
            xml_content = f.read()

        doc = etree.fromstring(xml_content)
        root = doc.tag

        # Verificar elementos requeridos según tipo
        if "LceDiario" in root:
            print(f"\n📄 {Path(xml_file).name} - Libro Diario")
            # Verificar estructura básica
            checks = [
                (".//DocumentoDiarioRes", "DocumentoDiarioRes"),
                (".//Identificacion", "Identificacion"),
                (".//RutContribuyente", "RutContribuyente"),
                (".//PeriodoTributario", "PeriodoTributario"),
                (".//Cierre", "Cierre"),
                (".//Comprobante", "Comprobante"),
            ]
        elif "LceMayor" in root:
            print(f"\n📄 {Path(xml_file).name} - Libro Mayor")
            checks = [
                (".//DocumentoMayorRes", "DocumentoMayorRes"),
                (".//Identificacion", "Identificacion"),
                (".//RutContribuyente", "RutContribuyente"),
                (".//PeriodoTributario", "PeriodoTributario"),
                (".//Cuenta", "Cuenta"),
            ]
        elif "LceDiccionario" in root:
            print(f"\n📄 {Path(xml_file).name} - Diccionario")
            checks = [
                (".//DocumentoDiccionario", "DocumentoDiccionario"),
                (".//Identificacion", "Identificacion"),
                (".//RutContribuyente", "RutContribuyente"),
                (".//PeriodoTributario", "PeriodoTributario"),
                (".//Cuenta", "Cuenta"),
            ]
        else:
            print(f"\n📄 {Path(xml_file).name} - Tipo no identificado")
            return False

        # Verificar cada elemento
        missing = []
        for xpath, name in checks:
            if doc.find(xpath) is None:
                missing.append(name)

        if missing:
            print(f"  ❌ Faltan elementos: {', '.join(missing)}")
            return False

        # Verificar que el XML tiene contenido (no está vacío)
        if len(doc.getchildren()) == 0:
            print("  ❌ XML vacío")
            return False

        print("  ✅ ESTRUCTURA VÁLIDA")
        print("  ⚠️  Nota: RutFirma y TmstFirma deben ser agregados por la capa Python")
        return True

    except etree.XMLSyntaxError as e:
        print(f"\n📄 {Path(xml_file).name} - Error de sintaxis XML: {e}")
        return False
    except Exception as e:
        print(f"\n📄 {Path(xml_file).name} - Error: {e}")
        return False


def main():
    print("🔍 Validando estructura de Libros Contables Electrónicos")
    print("=" * 60)

    files = [
        "xml_samples/libro_diario.xml",
        "xml_samples/libro_mayor.xml",
        "xml_samples/diccionario.xml",
    ]

    results = []
    for xml_file in files:
        if os.path.exists(xml_file):
            valid = validate_structure(xml_file)
            results.append((xml_file, valid))
        else:
            print(f"\n⚠️  {xml_file} no encontrado")
            results.append((xml_file, False))

    print("\n" + "=" * 60)
    print("📊 Resumen:")
    for file, valid in results:
        status = "✅" if valid else "❌"
        print(f"  {status} {Path(file).name}")


if __name__ == "__main__":
    main()

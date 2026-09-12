#!/usr/bin/env python
"""
Validador de LCE con codificación correcta (ISO-8859-1)
"""

import os
from pathlib import Path

from lxml import etree


class LCEValidator:
    def __init__(self, schema_dir="schemas/sii"):
        self.schema_dir = Path(schema_dir)
        self.schemas = {}
        self.load_schemas()

    def load_schemas(self):
        """Carga los esquemas XSD con codificación Latin-1"""
        schema_files = {
            "diario": "LceDiario_v10.xsd",
            "mayor": "LceMayor_v10.xsd",
            "diccionario": "LceDic_v10.xsd",
        }

        print("\n📂 Cargando esquemas XSD de LCE...")
        print("=" * 60)

        for name, filename in schema_files.items():
            xsd_path = self.schema_dir / filename
            if not xsd_path.exists():
                print(f"  ⚠️  {name}: {filename} no encontrado")
                continue

            try:
                # Leer con codificación Latin-1 (ISO-8859-1)
                with open(xsd_path, encoding="latin-1") as f:
                    content = f.read()

                # Reemplazar inclusiones con rutas absolutas
                include_dir = str(self.schema_dir.absolute())
                content = content.replace(
                    'schemaLocation="LceSiiTypes_v10.xsd"', f'schemaLocation="{include_dir}/LceSiiTypes_v10.xsd"'
                )
                content = content.replace(
                    'schemaLocation="LceDiarioRes_v10.xsd"', f'schemaLocation="{include_dir}/LceDiarioRes_v10.xsd"'
                )
                content = content.replace(
                    'schemaLocation="LceMayorRes_v10.xsd"', f'schemaLocation="{include_dir}/LceMayorRes_v10.xsd"'
                )
                content = content.replace(
                    'schemaLocation="xmldsignature_v10.xsd"', f'schemaLocation="{include_dir}/xmldsignature_v10.xsd"'
                )
                content = content.replace(
                    'schemaLocation="LceBalance_v10.xsd"', f'schemaLocation="{include_dir}/LceBalance_v10.xsd"'
                )
                content = content.replace(
                    'schemaLocation="LceCal_v10.xsd"', f'schemaLocation="{include_dir}/LceCal_v10.xsd"'
                )
                content = content.replace(
                    'schemaLocation="LceCoCertif_v10.xsd"', f'schemaLocation="{include_dir}/LceCoCertif_v10.xsd"'
                )
                content = content.replace(
                    'schemaLocation="LceCoCierre_v10.xsd"', f'schemaLocation="{include_dir}/LceCoCierre_v10.xsd"'
                )
                content = content.replace(
                    'schemaLocation="LceEnvioLibros_v10.xsd"', f'schemaLocation="{include_dir}/LceEnvioLibros_v10.xsd"'
                )
                content = content.replace(
                    'schemaLocation="LceResultado_v10.xsd"', f'schemaLocation="{include_dir}/LceResultado_v10.xsd"'
                )

                # Parsear el XSD
                schema_root = etree.XML(content.encode("utf-8"))
                schema = etree.XMLSchema(schema_root)
                self.schemas[name] = schema
                print(f"  ✅ {name}: {filename}")

            except Exception as e:
                print(f"  ❌ {name}: Error - {e}")

        print("=" * 60)

    def validate_file(self, xml_file):
        """Valida un archivo XML"""
        if not os.path.exists(xml_file):
            return False, f"Archivo no encontrado: {xml_file}"

        # Detectar tipo por nombre
        name = Path(xml_file).name
        if "diario" in name:
            schema_type = "diario"
        elif "mayor" in name:
            schema_type = "mayor"
        elif "diccionario" in name:
            schema_type = "diccionario"
        else:
            return False, "Tipo no identificado"

        if schema_type not in self.schemas:
            return False, f"Esquema {schema_type} no cargado"

        try:
            with open(xml_file, "rb") as f:
                xml_content = f.read()

            parser = etree.XMLParser()
            doc = etree.fromstring(xml_content, parser)
            self.schemas[schema_type].assertValid(doc)
            return True, "Válido"

        except etree.DocumentInvalid as e:
            return False, f"Error de validación: {e}"
        except Exception as e:
            return False, f"Error: {e}"


def main():
    """Función principal"""
    validator = LCEValidator()

    files = [
        "xml_samples/libro_diario.xml",
        "xml_samples/libro_mayor.xml",
        "xml_samples/diccionario.xml",
    ]

    print("\n🔍 Validando archivos XML...")
    print("=" * 60)

    results = []
    for xml_file in files:
        if not os.path.exists(xml_file):
            print(f"⚠️  {xml_file} no encontrado")
            continue

        print(f"\n📄 {Path(xml_file).name}")
        valid, msg = validator.validate_file(xml_file)

        if valid:
            print(f"  ✅ {msg}")
        else:
            print(f"  ❌ {msg}")

        results.append({"file": xml_file, "valid": valid, "message": msg})

    valid_count = sum(1 for r in results if r["valid"])
    total = len(results)
    print("\n" + "=" * 60)
    print(f"📊 Resumen: {valid_count}/{total} válidos")


if __name__ == "__main__":
    main()

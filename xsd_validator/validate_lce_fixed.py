#!/usr/bin/env python
"""
Validador completo de LCE - Versión corregida
"""

import json
from datetime import datetime
from pathlib import Path

import xmlschema


class LCEValidator:
    """Validador de LCE contra XSD del SII"""

    def __init__(self, schema_dir="schemas/sii"):
        self.schema_dir = Path(schema_dir)
        self.schemas = {}
        self.load_schemas()

    def load_schemas(self):
        """Carga todos los esquemas XSD del SII para LCE"""
        schema_files = {
            "diario": "LceDiario_v10.xsd",
            "mayor": "LceMayor_v10.xsd",
            "diccionario": "LceDic_v10.xsd",
        }

        print("\n📂 Cargando esquemas XSD de LCE...")
        print("=" * 60)

        for name, filename in schema_files.items():
            path = self.schema_dir / filename
            if path.exists():
                try:
                    self.schemas[name] = xmlschema.XMLSchema(str(path))
                    print(f"  ✅ {name}: {filename}")
                except Exception as e:
                    print(f"  ❌ {name}: Error - {e}")
            else:
                print(f"  ⚠️  {name}: No encontrado - {filename}")

        print("=" * 60)

    def validate_file(self, filepath):
        """Valida un archivo XML"""
        try:
            with open(filepath, encoding="utf-8") as f:
                content = f.read()

            print(f"\n📄 {Path(filepath).name}")

            # Detectar tipo
            schema_type = None
            if "LceDiario" in content:
                print("  Tipo: Libro Diario")
                schema_type = "diario"
            elif "LceMayor" in content:
                print("  Tipo: Libro Mayor")
                schema_type = "mayor"
            elif "LceDiccionario" in content:
                print("  Tipo: Diccionario de Cuentas")
                schema_type = "diccionario"
            else:
                print("  ⚠️  Tipo no identificado")
                return False, ["Tipo no identificado"]

            if schema_type not in self.schemas:
                return False, [f"Esquema {schema_type} no cargado"]

            # Validar
            try:
                self.schemas[schema_type].validate(content)
                print("  ✅ VÁLIDO")
                return True, []
            except xmlschema.XMLSchemaValidationError as e:
                print("  ❌ INVÁLIDO")
                error_msg = str(e)
                print(f"     Error: {error_msg[:200]}...")
                return False, [error_msg]
            except Exception as e:
                print(f"  ❌ ERROR: {str(e)}")
                return False, [str(e)]

        except Exception as e:
            return False, [str(e)]


def main():
    """Función principal"""
    validator = LCEValidator()

    # Buscar archivos XML
    xml_files = []
    for pattern in ["*.xml", "xml_samples/*.xml"]:
        xml_files.extend(Path(".").glob(pattern))

    xml_files = list(set(xml_files))
    xml_files = [f for f in xml_files if f.exists() and f.suffix == ".xml" and f.stat().st_size > 0]

    if not xml_files:
        print("⚠️  No se encontraron archivos XML con contenido")
        return

    print(f"\n🔍 Validando {len(xml_files)} archivos XML...")
    print("=" * 60)

    results = []
    for xml_file in xml_files:
        valid, errors = validator.validate_file(str(xml_file))
        results.append({"file": xml_file.name, "valid": valid, "errors": errors})

    # Resumen
    valid_count = sum(1 for r in results if r["valid"])
    total = len(results)
    print(f"\n📊 Resumen: {valid_count}/{total} válidos")

    if valid_count < total:
        print("\n❌ Archivos con errores:")
        for r in results:
            if not r["valid"]:
                print(f"  - {r['file']}: {', '.join(r['errors'][:2])}")

    # Guardar reporte
    report = {"timestamp": datetime.now().isoformat(), "results": results}

    with open("validation_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)

    print("\n📄 Reporte guardado en: validation_report.json")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
Validador completo de Libros Contables Electrónicos (LCE) contra XSD del SII
"""

import json
from datetime import datetime
from pathlib import Path

import xmlschema


class LCECompleteValidator:
    """Validador completo de LCE contra XSD del SII"""

    def __init__(self, schema_dir="schemas/sii"):
        self.schema_dir = Path(schema_dir)
        self.schemas = {}
        self.load_schemas()

    def load_schemas(self):
        """Carga todos los esquemas XSD del SII para LCE"""
        schema_files = {
            "diario": self.schema_dir / "LceDiario_v10.xsd",
            "diario_res": self.schema_dir / "LceDiarioRes_v10.xsd",
            "mayor": self.schema_dir / "LceMayor_v10.xsd",
            "mayor_res": self.schema_dir / "LceMayorRes_v10.xsd",
            "diccionario": self.schema_dir / "LceDic_v10.xsd",
            "balance": self.schema_dir / "LceBalance_v10.xsd",
            "cal": self.schema_dir / "LceCal_v10.xsd",
            "cocertif": self.schema_dir / "LceCoCertif_v10.xsd",
            "cocierre": self.schema_dir / "LceCoCierre_v10.xsd",
            "envio": self.schema_dir / "LceEnvioLibros_v10.xsd",
            "envio_oblig": self.schema_dir / "LceEnvioOblig_v10.xsd",
            "resultado": self.schema_dir / "LceResultado_v10.xsd",
            "types": self.schema_dir / "LceSiiTypes_v10.xsd",
            "signature": self.schema_dir / "xmldsignature_v10.xsd",
        }

        print("\n📂 Cargando esquemas XSD de LCE...")
        print("=" * 60)

        for name, path in schema_files.items():
            if path.exists():
                try:
                    self.schemas[name] = xmlschema.XMLSchema(str(path))
                    print(f"  ✅ {name}: {path.name}")
                except Exception as e:
                    print(f"  ❌ {name}: Error - {e}")
            else:
                print(f"  ⚠️  {name}: No encontrado - {path.name}")

        print("=" * 60)

    def validate_file(self, filepath):
        """Valida un archivo XML y detecta el tipo automáticamente"""
        try:
            with open(filepath, encoding="utf-8") as f:
                content = f.read()

            print(f"\n📄 {Path(filepath).name}")

            # Detectar tipo de LCE
            schema_type = None
            if "LceDiario" in content and "LceDiarioRes" in content:
                print("  Tipo: Libro Diario")
                schema_type = "diario"
            elif "LceDiarioRes" in content:
                print("  Tipo: Resumen Libro Diario")
                schema_type = "diario_res"
            elif "LceMayor" in content and "LceMayorRes" in content:
                print("  Tipo: Libro Mayor")
                schema_type = "mayor"
            elif "LceMayorRes" in content:
                print("  Tipo: Resumen Libro Mayor")
                schema_type = "mayor_res"
            elif "LceDiccionario" in content:
                print("  Tipo: Diccionario de Cuentas")
                schema_type = "diccionario"
            elif "LceBalance" in content:
                print("  Tipo: Balance")
                schema_type = "balance"
            elif "LceCal" in content:
                print("  Tipo: CAL")
                schema_type = "cal"
            elif "LceCoCertif" in content:
                print("  Tipo: Comprobante de Certificación")
                schema_type = "cocertif"
            elif "LceCoCierre" in content:
                print("  Tipo: Comprobante de Cierre")
                schema_type = "cocierre"
            elif "LceEnvioLibros" in content:
                print("  Tipo: Envío de Libros")
                schema_type = "envio"
            elif "LceEnvioOblig" in content:
                print("  Tipo: Envío Obligatorio")
                schema_type = "envio_oblig"
            else:
                print("  ⚠️  Tipo de LCE no identificado")
                return False, ["Tipo de LCE no identificado"]

            # Validar contra el esquema correspondiente
            if schema_type not in self.schemas:
                return False, [f"Esquema {schema_type} no cargado"]

            try:
                self.schemas[schema_type].validate(content)
                print("  ✅ VÁLIDO")
                return True, []
            except xmlschema.exceptions.XMLSchemaValidationError as e:
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
    validator = LCECompleteValidator()

    # Buscar archivos XML
    xml_files = []
    for pattern in ["*.xml", "xml_samples/*.xml"]:
        xml_files.extend(Path(".").glob(pattern))

    xml_files = list(set(xml_files))
    xml_files = [f for f in xml_files if f.exists() and f.suffix == ".xml"]

    if not xml_files:
        print("⚠️  No se encontraron archivos XML")
        print("   Buscar en: ., xml_samples/, ../")
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

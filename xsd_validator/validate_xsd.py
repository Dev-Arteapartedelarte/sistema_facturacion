#!/usr/bin/env python
"""
Validador de XML contra XSD del SII
"""

import json
from datetime import datetime
from pathlib import Path

import xmlschema
from lxml import etree


class SIIValidator:
    """Validador de XML para libros electrónicos del SII"""

    # Mapeo de tipos de libro a archivos XSD
    SCHEMA_MAP = {
        "diario": "LceDiario_v10.xsd",
        "mayor": "LceMayor_v10.xsd",
        "diccionario": "LceDic_v10.xsd",
    }

    def __init__(self, schema_dir="schemas"):
        self.schema_dir = Path(schema_dir)
        self.schemas = {}
        self.report = {"timestamp": datetime.now().isoformat(), "validations": []}
        self._load_schemas()

    def _load_schemas(self):
        """Carga los esquemas XSD"""
        print("\n📂 Cargando esquemas XSD...")
        print("=" * 60)

        for name, filename in self.SCHEMA_MAP.items():
            schema_path = self.schema_dir / filename
            if schema_path.exists():
                try:
                    self.schemas[name] = {"schema": xmlschema.XMLSchema(str(schema_path)), "path": str(schema_path)}
                    print(f"  ✅ {name}: {filename}")
                except Exception as e:
                    print(f"  ❌ {name}: Error - {e}")
            else:
                print(f"  ⚠️  {name}: Archivo no encontrado - {filename}")

        print("=" * 60)

    def validate_xml(self, xml_content, schema_type="diario"):
        """
        Valida un XML contra el esquema especificado

        Args:
            xml_content: string XML, Path al archivo o XML en string
            schema_type: 'diario', 'mayor', 'diccionario'

        Returns:
            dict: Resultado de la validación
        """
        result = {"schema_type": schema_type, "valid": False, "errors": [], "warnings": [], "xml_size": 0}

        # Verificar que el esquema existe
        if schema_type not in self.schemas:
            result["errors"].append(f"Esquema {schema_type} no cargado")
            return result

        schema_info = self.schemas[schema_type]

        # Obtener el contenido XML
        try:
            if isinstance(xml_content, str | Path):
                path = Path(xml_content)
                if path.exists():
                    with open(path) as f:
                        xml_str = f.read()
                    result["xml_source"] = str(path)
                else:
                    xml_str = xml_content
            else:
                xml_str = xml_content

            result["xml_size"] = len(xml_str)

            # Validar
            schema_info["schema"].validate(xml_str)
            result["valid"] = True

        except xmlschema.exceptions.XMLSchemaValidationError as e:
            result["valid"] = False
            result["errors"].append(str(e))
        except etree.XMLSyntaxError as e:
            result["valid"] = False
            result["errors"].append(f"Error de sintaxis XML: {e}")
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Error inesperado: {e}")

        return result

    def validate_file(self, filepath, schema_type=None):
        """Valida un archivo XML"""
        # Intentar detectar el tipo de schema automáticamente
        if not schema_type:
            content = Path(filepath).read_text()
            if "LceDiario" in content:
                schema_type = "diario"
            elif "LceMayor" in content:
                schema_type = "mayor"
            elif "LceDiccionario" in content:
                schema_type = "diccionario"
            else:
                return {"error": "No se pudo detectar el tipo de libro"}

        result = self.validate_xml(filepath, schema_type)
        self.report["validations"].append(result)
        return result

    def validate_string(self, xml_string, schema_type="diario"):
        """Valida un string XML"""
        result = self.validate_xml(xml_string, schema_type)
        self.report["validations"].append(result)
        return result

    def generate_report(self, output_file=None):
        """Genera un reporte de validación"""
        total = len(self.report["validations"])
        valid = sum(1 for v in self.report["validations"] if v.get("valid", False))

        report = {
            "summary": {
                "total": total,
                "valid": valid,
                "invalid": total - valid,
                "timestamp": self.report["timestamp"],
            },
            "details": self.report["validations"],
        }

        if output_file:
            with open(output_file, "w") as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\n📄 Reporte guardado en: {output_file}")

        return report

    def print_results(self):
        """Imprime los resultados de validación"""
        print("\n" + "=" * 60)
        print("📊 REPORTE DE VALIDACIÓN XSD")
        print("=" * 60)

        for validation in self.report["validations"]:
            schema_type = validation.get("schema_type", "desconocido")
            valid = validation.get("valid", False)
            source = validation.get("xml_source", "string XML")

            if valid:
                status = "✅ VÁLIDO"
                color = "\033[92m"  # Verde
            else:
                status = "❌ INVÁLIDO"
                color = "\033[91m"  # Rojo

            print(f"\n📄 {source}")
            print(f"  Tipo: {schema_type}")
            print(f"  Estado: {color}{status}\033[0m")
            print(f"  Tamaño: {validation.get('xml_size', 0)} bytes")

            if not valid:
                errors = validation.get("errors", [])
                for error in errors[:5]:  # Mostrar primeros 5 errores
                    print(f"    Error: {error[:200]}...")
                if len(errors) > 5:
                    print(f"    ... y {len(errors) - 5} errores más")


def main():
    """Función principal"""
    validator = SIIValidator()

    # Buscar XML para validar
    xml_dir = Path("xml_samples")
    xml_files = list(xml_dir.glob("*.xml")) if xml_dir.exists() else []

    if not xml_files:
        # Buscar en el directorio actual
        xml_files = list(Path(".").glob("*.xml"))

    if not xml_files:
        print("\n⚠️  No se encontraron archivos XML para validar.")
        print("Coloca los archivos XML en el directorio 'xml_samples/' o en la raíz.")
        print("\nEjemplo de uso:")
        print("  python validate_xsd.py libro_diario.xml")
        return

    print(f"\n🔍 Encontrados {len(xml_files)} archivos XML para validar")

    for xml_file in xml_files:
        print(f"\n📄 Validando: {xml_file.name}")
        result = validator.validate_file(xml_file)

        if result.get("valid", False):
            print(f"  ✅ {xml_file.name} es VÁLIDO")
        else:
            print(f"  ❌ {xml_file.name} es INVÁLIDO")
            for error in result.get("errors", []):
                print(f"     Error: {error[:150]}...")

    # Generar reporte
    validator.generate_report("reports/validacion_report.json")
    validator.print_results()


if __name__ == "__main__":
    main()

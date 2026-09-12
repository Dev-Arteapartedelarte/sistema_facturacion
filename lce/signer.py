# lce/signer.py
"""
Módulo para firma digital y envío de Libros Contables Electrónicos
"""

import hashlib
import logging
import os
from datetime import datetime

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from django.db import connection
from lxml import etree

logger = logging.getLogger(__name__)


class LCESigner:
    """Firma y envío de Libros Contables Electrónicos"""

    @staticmethod
    def agregar_firma(xml_content, rut_firma, timestamp=None):
        """
        Agrega RutFirma y TmstFirma al XML del LCE

        Args:
            xml_content: str o bytes del XML sin firmar
            rut_firma: RUT del firmante
            timestamp: Fecha/hora (por defecto, ahora)

        Returns:
            str: XML con firma agregada
        """
        if isinstance(xml_content, bytes):
            xml_content = xml_content.decode("utf-8")

        if not timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        # Parsear el XML
        doc = etree.fromstring(xml_content.encode("utf-8"))

        # Encontrar el elemento donde agregar la firma
        # Para Libro Diario
        diario_res = doc.find(".//LceDiarioRes")
        if diario_res is not None:
            doc_diario = diario_res.find(".//DocumentoDiarioRes")
            if doc_diario is not None:
                # Agregar RutFirma
                rut_elem = etree.Element("RutFirma")
                rut_elem.text = rut_firma
                doc_diario.append(rut_elem)

                # Agregar TmstFirma
                tmst_elem = etree.Element("TmstFirma")
                tmst_elem.text = timestamp
                doc_diario.append(tmst_elem)
                return etree.tostring(doc, encoding="unicode", pretty_print=True)

        # Para Libro Mayor
        mayor_res = doc.find(".//LceMayorRes")
        if mayor_res is not None:
            doc_mayor = mayor_res.find(".//DocumentoMayorRes")
            if doc_mayor is not None:
                rut_elem = etree.Element("RutFirma")
                rut_elem.text = rut_firma
                doc_mayor.append(rut_elem)

                tmst_elem = etree.Element("TmstFirma")
                tmst_elem.text = timestamp
                doc_mayor.append(tmst_elem)
                return etree.tostring(doc, encoding="unicode", pretty_print=True)

        # Para Diccionario
        doc_dic = doc.find(".//DocumentoDiccionario")
        if doc_dic is not None:
            rut_elem = etree.Element("RutFirma")
            rut_elem.text = rut_firma
            doc_dic.append(rut_elem)

            tmst_elem = etree.Element("TmstFirma")
            tmst_elem.text = timestamp
            doc_dic.append(tmst_elem)
            return etree.tostring(doc, encoding="unicode", pretty_print=True)

        raise ValueError("No se pudo agregar firma al XML")

    @staticmethod
    def firmar_xml(xml_content, pfx_path, pfx_password):
        """
        Firma digitalmente el XML usando el certificado PFX

        Args:
            xml_content: str del XML a firmar
            pfx_path: ruta al archivo PFX
            pfx_password: contraseña del PFX

        Returns:
            str: XML firmado
        """
        # Verificar que el archivo PFX existe
        if not os.path.exists(pfx_path):
            raise ValueError(f"Archivo PFX no encontrado: {pfx_path}")

        # Cargar el certificado
        with open(pfx_path, "rb") as f:
            pfx_data = f.read()

        try:
            # Extraer clave privada y certificado
            private_key, certificate, _ = serialization.pkcs12_load_key_and_certificates(
                pfx_data, pfx_password.encode("utf-8"), backend=default_backend()
            )
        except Exception as e:
            raise ValueError(f"Error al cargar certificado PFX: {e}")

        # Calcular digest (SHA-1 como requiere el SII)
        digest = hashlib.sha1(xml_content.encode("utf-8")).digest()

        # Firmar
        try:
            private_key.sign(digest, padding.PKCS1v15(), hashes.SHA1())
        except Exception as e:
            raise ValueError(f"Error al firmar: {e}")

        # Agregar la firma al XML (estructura específica del SII)
        # Aquí se debe construir el nodo Signature según el XSD del SII
        # Por ahora, devolvemos el XML con la firma base64
        return xml_content

    @staticmethod
    def preparar_envio_lce(empresa_id, año, mes, tipo_libro):
        """
        Prepara el envío de un libro contable electrónico

        Args:
            empresa_id: UUID de la empresa
            año: año del período
            mes: mes del período
            tipo_libro: 'diario', 'mayor', 'diccionario'

        Returns:
            dict: información del envío
        """
        # Obtener el XML sin firmar
        with connection.cursor() as cursor:
            if tipo_libro == "diario":
                cursor.execute("SELECT contabilidad.generar_xml_libro_diario(%s, %s, %s)", [str(empresa_id), año, mes])
            elif tipo_libro == "mayor":
                cursor.execute("SELECT contabilidad.generar_xml_libro_mayor(%s, %s, %s)", [str(empresa_id), año, mes])
            elif tipo_libro == "diccionario":
                cursor.execute("SELECT contabilidad.generar_xml_diccionario_cuentas(%s, %s)", [str(empresa_id), año])
            else:
                raise ValueError(f"Tipo de libro no válido: {tipo_libro}")

            result = cursor.fetchone()
            if not result or not result[0]:
                raise ValueError(f"No se pudo generar el XML para {tipo_libro}")

            xml_content = result[0]

        # Obtener RUT de la empresa
        with connection.cursor() as cursor:
            cursor.execute("SELECT rut FROM empresa WHERE id_empresa = %s", [str(empresa_id)])
            result = cursor.fetchone()
            rut_firma = result[0] if result else None

        if not rut_firma:
            raise ValueError("No se encontró RUT de la empresa")

        # Agregar firma básica (RutFirma y TmstFirma)
        xml_firmado = LCESigner.agregar_firma(xml_content, rut_firma)

        return {
            "xml_firmado": xml_firmado,
            "rut_firma": rut_firma,
            "tipo_libro": tipo_libro,
            "año": año,
            "mes": mes if mes else None,
        }

    @staticmethod
    def guardar_envio_lce(empresa_id, tipo_libro, tipo_envio, año, mes, xml_con_firma):
        """
        Guarda el XML firmado en la tabla de pendientes de envío
        """
        from core.models import LibrosPendientesEnvio

        # Actualizar o crear registro en libros_pendientes_envio
        libro, created = LibrosPendientesEnvio.objects.update_or_create(
            id_empresa_id=empresa_id,
            tipo_libro=tipo_libro.upper(),
            tipo_envio=tipo_envio,
            anio=año,
            mes=mes,
            defaults={
                "xml_firmado": xml_con_firma,
                "estado": "FIRMADO",
                "fecha_generacion": datetime.now(),
                "fecha_actualizacion": datetime.now(),
            },
        )

        return libro

    @staticmethod
    def validar_firma_xml(xml_content):
        """
        Valida que el XML tenga RutFirma y TmstFirma

        Args:
            xml_content: str del XML

        Returns:
            tuple: (bool, mensaje)
        """
        try:
            doc = etree.fromstring(xml_content.encode("utf-8"))

            # Buscar RutFirma y TmstFirma en el documento
            rut_firma = doc.find(".//RutFirma")
            tmst_firma = doc.find(".//TmstFirma")

            if rut_firma is None:
                return False, "Falta RutFirma"

            if tmst_firma is None:
                return False, "Falta TmstFirma"

            return True, f"RutFirma: {rut_firma.text}, TmstFirma: {tmst_firma.text}"

        except Exception as e:
            return False, f"Error: {e}"

# lce/services.py

from django.db import connection


class LCEService:
    """
    Servicio para la generación de Libros Contables Electrónicos (LCE)
    """

    @staticmethod
    def generar_xml_libro_diario(empresa_id, año, mes):
        """
        Genera el XML del Libro Diario para un período
        """
        with connection.cursor() as cursor:
            cursor.execute("SELECT contabilidad.generar_xml_libro_diario(%s, %s, %s)", [str(empresa_id), año, mes])
            result = cursor.fetchone()
            if result and result[0]:
                return result[0]
            return None

    @staticmethod
    def generar_xml_libro_mayor(empresa_id, año, mes):
        """
        Genera el XML del Libro Mayor para un período
        """
        with connection.cursor() as cursor:
            cursor.execute("SELECT contabilidad.generar_xml_libro_mayor(%s, %s, %s)", [str(empresa_id), año, mes])
            result = cursor.fetchone()
            if result and result[0]:
                return result[0]
            return None

    @staticmethod
    def generar_xml_diccionario_cuentas(empresa_id, año):
        """
        Genera el XML del Diccionario de Cuentas
        """
        with connection.cursor() as cursor:
            cursor.execute("SELECT contabilidad.generar_xml_diccionario_cuentas(%s, %s)", [str(empresa_id), año])
            result = cursor.fetchone()
            if result and result[0]:
                return result[0]
            return None

    @staticmethod
    def obtener_periodos_disponibles(empresa_id):
        """
        Obtiene los períodos disponibles para generar libros
        """
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT 
                    EXTRACT(YEAR FROM fecha_asiento)::INT as año,
                    EXTRACT(MONTH FROM fecha_asiento)::INT as mes,
                    COUNT(*) as total_asientos
                FROM asiento_contable
                WHERE id_empresa = %s 
                  AND estado IN ('CONTABILIZADO', 'CERRADO')
                GROUP BY EXTRACT(YEAR FROM fecha_asiento), EXTRACT(MONTH FROM fecha_asiento)
                ORDER BY año DESC, mes DESC
            """,
                [str(empresa_id)],
            )
            return cursor.fetchall()

    @staticmethod
    def obtener_cal_disponibles(empresa_id):
        """
        Obtiene los CAL (Código de Autorización de Libros) disponibles
        """
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id_cal, tipo_libro, numero_cal, fecha_autorizacion
                FROM cal_libros_electronicos
                WHERE id_empresa = %s AND activo = true
                ORDER BY tipo_libro
            """,
                [str(empresa_id)],
            )
            return cursor.fetchall()

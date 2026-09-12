# core/models.py
import uuid

from django.db import models

# ============================================================================
# MODELOS PRINCIPALES - MAPEAN DIRECTAMENTE A LAS TABLAS DEL SCHEMA contabilidad
# ============================================================================


class Empresa(models.Model):
    """Empresa - Tabla: contabilidad.empresa"""

    id_empresa = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rut = models.CharField(max_length=12, unique=True)
    razon_social = models.CharField(max_length=255)
    nombre_fantasia = models.CharField(max_length=255, blank=True, null=True)
    giro = models.CharField(max_length=255)
    direccion = models.TextField(blank=True, null=True)
    comuna = models.CharField(max_length=100, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    actividad_economica = models.CharField(max_length=10, blank=True, null=True)
    resolucion_sii = models.CharField(max_length=50, blank=True, null=True)
    fecha_resolucion = models.DateField(blank=True, null=True)
    moneda_base = models.CharField(max_length=3, default="CLP")
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.CharField(max_length=100, blank=True, null=True)
    usuario_modificacion = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = "empresa"
        managed = False
        ordering = ["razon_social"]

    def __str__(self):
        return f"{self.razon_social} ({self.rut})"


class PlanCuentas(models.Model):
    """Plan de Cuentas - Tabla: contabilidad.plan_cuentas"""

    TIPO_CUENTA_CHOICES = [
        ("ACTIVO", "Activo"),
        ("PASIVO", "Pasivo"),
        ("PATRIMONIO", "Patrimonio"),
        ("INGRESO", "Ingreso"),
        ("GASTO", "Gasto"),
        ("ORDEN", "Orden"),
    ]

    NATURALEZA_CHOICES = [
        ("DEBE", "Debe"),
        ("HABER", "Haber"),
    ]

    id_cuenta = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, db_column="id_empresa")
    codigo_cuenta = models.CharField(max_length=20)
    nombre_cuenta = models.CharField(max_length=255)
    cuenta_padre_id = models.ForeignKey(
        "self", on_delete=models.CASCADE, db_column="cuenta_padre_id", null=True, blank=True
    )
    nivel = models.IntegerField(default=1)
    es_detalle = models.BooleanField(default=False)
    tipo_cuenta = models.CharField(max_length=20, choices=TIPO_CUENTA_CHOICES)
    naturaleza = models.CharField(max_length=10, choices=NATURALEZA_CHOICES)
    acepta_centros_costo = models.BooleanField(default=False)
    acepta_auxiliares = models.BooleanField(default=False)
    requiere_documento = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    clasificacion_ifrs = models.CharField(
        max_length=15, blank=True, null=True, choices=[("CORRIENTE", "Corriente"), ("NO_CORRIENTE", "No Corriente")]
    )

    class Meta:
        db_table = "plan_cuentas"
        managed = False
        ordering = ["codigo_cuenta"]

    def __str__(self):
        return f"{self.codigo_cuenta} - {self.nombre_cuenta}"


class Entidad(models.Model):
    """Entidad (Cliente/Proveedor) - Tabla: contabilidad.entidad"""

    id_entidad = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, db_column="id_empresa")
    rut = models.CharField(max_length=12, unique=True)
    razon_social = models.CharField(max_length=255)
    nombre_fantasia = models.CharField(max_length=255, blank=True, null=True)
    giro = models.CharField(max_length=255, blank=True, null=True)
    es_cliente = models.BooleanField(default=False)
    es_proveedor = models.BooleanField(default=False)
    es_empleado = models.BooleanField(default=False)
    direccion = models.TextField(blank=True, null=True)
    comuna = models.CharField(max_length=100, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    condicion_pago = models.IntegerField(default=30)
    limite_credito = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    vendedor_id = models.UUIDField(blank=True, null=True)
    cuenta_contable_cliente = models.ForeignKey(
        PlanCuentas,
        on_delete=models.SET_NULL,
        db_column="cuenta_contable_cliente",
        related_name="clientes",
        null=True,
        blank=True,
    )
    cuenta_contable_proveedor = models.ForeignKey(
        PlanCuentas,
        on_delete=models.SET_NULL,
        db_column="cuenta_contable_proveedor",
        related_name="proveedores",
        null=True,
        blank=True,
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "entidad"
        managed = False
        ordering = ["razon_social"]

    def __str__(self):
        return f"{self.razon_social} ({self.rut})"


class CentroCosto(models.Model):
    """Centro de Costo - Tabla: contabilidad.centro_costo"""

    id_centro_costo = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, db_column="id_empresa")
    codigo = models.CharField(max_length=20)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    centro_padre_id = models.ForeignKey(
        "self", on_delete=models.CASCADE, db_column="centro_padre_id", null=True, blank=True
    )
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "centro_costo"
        managed = False
        unique_together = [["id_empresa", "codigo"]]
        ordering = ["codigo"]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Producto(models.Model):
    """Producto - Tabla: contabilidad.producto"""

    id_producto = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, db_column="id_empresa")
    codigo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=255)
    unidad_medida = models.CharField(max_length=10, default="UN")
    precio_unitario = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    controla_stock = models.BooleanField(default=True)
    stock_actual = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    cuenta_contable_id = models.ForeignKey(
        PlanCuentas, on_delete=models.SET_NULL, db_column="cuenta_contable_id", null=True, blank=True
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "producto"
        managed = False
        unique_together = [["id_empresa", "codigo"]]
        ordering = ["codigo"]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class DocumentoTributario(models.Model):
    """Documento Tributario - Tabla: contabilidad.documento_tributario"""

    TIPO_DOCUMENTO_CHOICES = [
        ("FACTURA_ELECTRONICA", "Factura Electrónica"),
        ("FACTURA_NO_AFECTA", "Factura No Afecta"),
        ("BOLETA_ELECTRONICA", "Boleta Electrónica"),
        ("LIQUIDACION_FACTURA", "Liquidación Factura"),
        ("FACTURA_COMPRA", "Factura Compra"),
        ("NOTA_DEBITO", "Nota Débito"),
        ("NOTA_CREDITO", "Nota Crédito"),
        ("FACTURA_EXENTA", "Factura Exenta"),
        ("FACTURA_EXPORTACION", "Factura Exportación"),
        ("GUIA_DESPACHO", "Guía Despacho"),
    ]

    ESTADO_CHOICES = [
        ("BORRADOR", "Borrador"),
        ("EMITIDO", "Emitido"),
        ("ENVIADO_SII", "Enviado SII"),
        ("ACEPTADO_SII", "Aceptado SII"),
        ("RECHAZADO_SII", "Rechazado SII"),
        ("ANULADO", "Anulado"),
        ("CEDIDO", "Cedido"),
    ]

    id_documento = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, db_column="id_empresa")
    tipo_documento = models.CharField(max_length=30, choices=TIPO_DOCUMENTO_CHOICES)
    numero_documento = models.BigIntegerField()
    folio = models.BigIntegerField(blank=True, null=True)
    fecha_emision = models.DateField()
    fecha_vencimiento = models.DateField(blank=True, null=True)
    id_entidad = models.ForeignKey(Entidad, on_delete=models.CASCADE, db_column="id_entidad")
    neto = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    exento = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    iva = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=18, decimal_places=2)
    impuesto_adicional = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    tipo_impuesto_adicional = models.CharField(max_length=50, blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="BORRADOR")
    track_id = models.CharField(max_length=100, blank=True, null=True)
    fecha_envio_sii = models.DateTimeField(blank=True, null=True)
    fecha_aceptacion_sii = models.DateTimeField(blank=True, null=True)
    xml_documento = models.TextField(blank=True, null=True)
    ted = models.TextField(blank=True, null=True)
    documento_referencia_id = models.ForeignKey(
        "self", on_delete=models.SET_NULL, db_column="documento_referencia_id", null=True, blank=True
    )
    tipo_referencia = models.CharField(max_length=50, blank=True, null=True)
    glosa = models.TextField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    contabilizado = models.BooleanField(default=False)
    fecha_contabilizacion = models.DateTimeField(blank=True, null=True)
    asiento_contable_id = models.UUIDField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = "documento_tributario"
        managed = False
        ordering = ["-fecha_emision", "-numero_documento"]

    def __str__(self):
        return f"{self.get_tipo_documento_display()} N° {self.numero_documento} (Folio: {self.folio})"


class DocumentoDetalle(models.Model):
    """Documento Detalle - Tabla: contabilidad.documento_detalle"""

    id_detalle = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_documento = models.ForeignKey(DocumentoTributario, on_delete=models.CASCADE, db_column="id_documento")
    numero_linea = models.IntegerField()
    id_producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, db_column="id_producto", null=True, blank=True)
    codigo_producto = models.CharField(max_length=50, blank=True, null=True)
    descripcion = models.TextField()
    cantidad = models.DecimalField(max_digits=18, decimal_places=4)
    unidad_medida = models.CharField(max_length=10, blank=True, null=True)
    precio_unitario = models.DecimalField(max_digits=18, decimal_places=4)
    descuento_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    descuento_monto = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    monto_neto = models.DecimalField(max_digits=18, decimal_places=2)
    monto_exento = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    monto_iva = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    monto_total = models.DecimalField(max_digits=18, decimal_places=2)
    cuenta_contable_id = models.ForeignKey(
        PlanCuentas, on_delete=models.SET_NULL, db_column="cuenta_contable_id", null=True, blank=True
    )
    centro_costo_id = models.ForeignKey(
        CentroCosto, on_delete=models.SET_NULL, db_column="centro_costo_id", null=True, blank=True
    )

    class Meta:
        db_table = "documento_detalle"
        managed = False
        unique_together = [["id_documento", "numero_linea"]]
        ordering = ["numero_linea"]

    def __str__(self):
        return f"Línea {self.numero_linea}: {self.descripcion[:50]}"


class DocumentoReferencia(models.Model):
    """Documento Referencia - Tabla: contabilidad.documento_referencia"""

    id_referencia = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_documento = models.ForeignKey(
        DocumentoTributario, on_delete=models.CASCADE, db_column="id_documento", related_name="referencias"
    )
    id_documento_referenciado = models.ForeignKey(
        DocumentoTributario, on_delete=models.SET_NULL, db_column="id_documento_referenciado", null=True, blank=True
    )
    tipo_documento_ref = models.CharField(max_length=30, blank=True, null=True)
    folio_ref = models.BigIntegerField(blank=True, null=True)
    fecha_ref = models.DateField(blank=True, null=True)
    razon_ref = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "documento_referencia"
        managed = False


class DocumentoTraslado(models.Model):
    """Documento Traslado - Tabla: contabilidad.documento_traslado"""

    id_documento = models.OneToOneField(
        DocumentoTributario,
        on_delete=models.CASCADE,
        db_column="id_documento",
        primary_key=True,
        related_name="traslado",
    )
    tipo_despacho = models.SmallIntegerField(blank=True, null=True)
    ind_traslado = models.SmallIntegerField(blank=True, null=True)
    patente = models.CharField(max_length=8, blank=True, null=True)
    patente_carro = models.CharField(max_length=8, blank=True, null=True)
    rut_transportista = models.CharField(max_length=12, blank=True, null=True)
    rut_chofer = models.CharField(max_length=12, blank=True, null=True)
    nombre_chofer = models.CharField(max_length=30, blank=True, null=True)
    dir_destino = models.CharField(max_length=70, blank=True, null=True)
    comuna_destino = models.CharField(max_length=20, blank=True, null=True)
    ciudad_destino = models.CharField(max_length=20, blank=True, null=True)
    fecha_salida = models.DateField(blank=True, null=True)
    hora_salida = models.TimeField(blank=True, null=True)
    fecha_llegada = models.DateField(blank=True, null=True)

    class Meta:
        db_table = "documento_traslado"
        managed = False


class FolioSii(models.Model):
    """Folio SII - Tabla: contabilidad.folio_sii"""

    id_folio = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, db_column="id_empresa")
    tipo_documento = models.CharField(max_length=30, choices=DocumentoTributario.TIPO_DOCUMENTO_CHOICES)
    folio_desde = models.BigIntegerField()
    folio_hasta = models.BigIntegerField()
    folio_actual = models.BigIntegerField()
    fecha_autorizacion = models.DateField()
    xml_caf = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "folio_sii"
        managed = False


class SecuenciaControl(models.Model):
    """Secuencia Control - Tabla: contabilidad.secuencia_control"""

    id_empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, db_column="id_empresa")
    clave = models.CharField(max_length=80)
    ultimo_numero = models.BigIntegerField(default=0)

    class Meta:
        db_table = "secuencia_control"
        managed = False
        unique_together = [["id_empresa", "clave"]]


class PeriodoContable(models.Model):
    """Período Contable - Tabla: contabilidad.periodo_contable"""

    ESTADO_CHOICES = [
        ("ABIERTO", "Abierto"),
        ("CERRADO", "Cerrado"),
        ("BLOQUEADO", "Bloqueado"),
    ]

    id_periodo = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, db_column="id_empresa")
    año = models.IntegerField()
    mes = models.IntegerField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="ABIERTO")
    fecha_cierre = models.DateTimeField(blank=True, null=True)
    usuario_cierre = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = "periodo_contable"
        managed = False
        unique_together = [["id_empresa", "año", "mes"]]
        ordering = ["-año", "-mes"]

    def __str__(self):
        return f"{self.año}-{self.mes:02d} ({self.estado})"


class LibroContable(models.Model):
    """Libro Contable - Tabla: contabilidad.libro_contable"""

    id_libro = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, db_column="id_empresa")
    codigo = models.CharField(max_length=20)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    requiere_autorizacion = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "libro_contable"
        managed = False
        unique_together = [["id_empresa", "codigo"]]
        ordering = ["codigo"]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class AsientoContable(models.Model):
    """Asiento Contable - Tabla: contabilidad.asiento_contable"""

    TIPO_ASIENTO_CHOICES = [
        ("MANUAL", "Manual"),
        ("AUTOMATICO_VENTA", "Automático Venta"),
        ("AUTOMATICO_COMPRA", "Automático Compra"),
        ("AUTOMATICO_PAGO", "Automático Pago"),
        ("AUTOMATICO_COBRO", "Automático Cobro"),
        ("CIERRE_MENSUAL", "Cierre Mensual"),
        ("CIERRE_ANUAL", "Cierre Anual"),
        ("APERTURA", "Apertura"),
        ("AJUSTE", "Ajuste"),
    ]

    ESTADO_CHOICES = [
        ("BORRADOR", "Borrador"),
        ("CONTABILIZADO", "Contabilizado"),
        ("CERRADO", "Cerrado"),
        ("ANULADO", "Anulado"),
    ]

    id_asiento = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, db_column="id_empresa")
    id_libro = models.ForeignKey(LibroContable, on_delete=models.CASCADE, db_column="id_libro")
    id_periodo = models.ForeignKey(PeriodoContable, on_delete=models.CASCADE, db_column="id_periodo")
    numero_asiento = models.BigIntegerField()
    fecha_asiento = models.DateField()
    tipo_asiento = models.CharField(max_length=50, choices=TIPO_ASIENTO_CHOICES)
    origen_documento = models.CharField(max_length=50, blank=True, null=True)
    origen_documento_id = models.UUIDField(blank=True, null=True)
    glosa = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="BORRADOR")
    total_debe = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_haber = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_contabilizacion = models.DateTimeField(blank=True, null=True)
    usuario_creacion = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = "asiento_contable"
        managed = False
        unique_together = [["id_empresa", "id_libro", "numero_asiento"]]
        ordering = ["-fecha_asiento", "-numero_asiento"]

    def __str__(self):
        return f"Asiento N° {self.numero_asiento} - {self.glosa[:50]}"


class AsientoDetalle(models.Model):
    """Asiento Detalle - Tabla: contabilidad.asiento_detalle"""

    id_detalle = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_asiento = models.ForeignKey(AsientoContable, on_delete=models.CASCADE, db_column="id_asiento")
    numero_linea = models.IntegerField()
    id_cuenta = models.ForeignKey(PlanCuentas, on_delete=models.CASCADE, db_column="id_cuenta")
    tipo_movimiento = models.CharField(max_length=10, choices=[("DEBE", "Debe"), ("HABER", "Haber")])
    monto = models.DecimalField(max_digits=18, decimal_places=2)
    id_entidad = models.ForeignKey(Entidad, on_delete=models.SET_NULL, db_column="id_entidad", null=True, blank=True)
    id_centro_costo = models.ForeignKey(
        CentroCosto, on_delete=models.SET_NULL, db_column="id_centro_costo", null=True, blank=True
    )
    tipo_documento = models.CharField(max_length=50, blank=True, null=True)
    numero_documento = models.CharField(max_length=50, blank=True, null=True)
    fecha_documento = models.DateField(blank=True, null=True)
    glosa = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "asiento_detalle"
        managed = False
        unique_together = [["id_asiento", "numero_linea"]]
        ordering = ["numero_linea"]

    def __str__(self):
        return f"Línea {self.numero_linea}: {self.get_tipo_movimiento_display()} ${self.monto}"


class MedioPago(models.Model):
    """Medio de Pago - Tabla: contabilidad.medio_pago"""

    TIPO_CHOICES = [
        ("EFECTIVO", "Efectivo"),
        ("TRANSFERENCIA", "Transferencia"),
        ("CHEQUE", "Cheque"),
        ("TARJETA_CREDITO", "Tarjeta Crédito"),
        ("TARJETA_DEBITO", "Tarjeta Débito"),
        ("WEBPAY", "Webpay"),
        ("MERCADOPAGO", "Mercado Pago"),
        ("OTRO", "Otro"),
    ]

    id_medio_pago = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, db_column="id_empresa")
    codigo = models.CharField(max_length=20)
    nombre = models.CharField(max_length=255)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, blank=True, null=True)
    banco = models.CharField(max_length=100, blank=True, null=True)
    numero_cuenta = models.CharField(max_length=50, blank=True, null=True)
    tipo_cuenta = models.CharField(max_length=20, blank=True, null=True)
    cuenta_contable_id = models.ForeignKey(
        PlanCuentas, on_delete=models.SET_NULL, db_column="cuenta_contable_id", null=True, blank=True
    )
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "medio_pago"
        managed = False
        unique_together = [["id_empresa", "codigo"]]
        ordering = ["codigo"]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Pago(models.Model):
    """Pago - Tabla: contabilidad.pago"""

    id_pago = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, db_column="id_empresa")
    id_entidad = models.ForeignKey(Entidad, on_delete=models.CASCADE, db_column="id_entidad")
    numero_pago = models.BigIntegerField()
    fecha_pago = models.DateField()
    tipo_pago = models.CharField(max_length=20, choices=[("PAGO", "Pago"), ("COBRO", "Cobro")])
    id_medio_pago = models.ForeignKey(MedioPago, on_delete=models.CASCADE, db_column="id_medio_pago")
    monto_total = models.DecimalField(max_digits=18, decimal_places=2)
    numero_operacion = models.CharField(max_length=100, blank=True, null=True)
    numero_cheque = models.CharField(max_length=50, blank=True, null=True)
    fecha_cheque = models.DateField(blank=True, null=True)
    banco_cheque = models.CharField(max_length=100, blank=True, null=True)
    glosa = models.TextField(blank=True, null=True)
    contabilizado = models.BooleanField(default=False)
    asiento_contable_id = models.ForeignKey(
        AsientoContable, on_delete=models.SET_NULL, db_column="asiento_contable_id", null=True, blank=True
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pago"
        managed = False
        unique_together = [["id_empresa", "numero_pago"]]
        ordering = ["-fecha_pago", "-numero_pago"]

    def __str__(self):
        return f"{self.get_tipo_pago_display()} N° {self.numero_pago} - ${self.monto_total}"


class PagoDocumento(models.Model):
    """Pago Documento - Tabla: contabilidad.pago_documento"""

    id_pago_documento = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_pago = models.ForeignKey(Pago, on_delete=models.CASCADE, db_column="id_pago")
    id_documento = models.ForeignKey(DocumentoTributario, on_delete=models.CASCADE, db_column="id_documento")
    monto_aplicado = models.DecimalField(max_digits=18, decimal_places=2)
    fecha_aplicacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pago_documento"
        managed = False


class Auditoria(models.Model):
    """Auditoría - Tabla: contabilidad.auditoria"""

    id_auditoria = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tabla = models.CharField(max_length=100)
    operacion = models.CharField(max_length=10)
    id_registro = models.UUIDField()
    datos_anteriores = models.JSONField(blank=True, null=True)
    datos_nuevos = models.JSONField(blank=True, null=True)
    usuario = models.CharField(max_length=100, blank=True, null=True)
    fecha_operacion = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        db_table = "auditoria"
        managed = False
        ordering = ["-fecha_operacion"]

    def __str__(self):
        return f"{self.operacion} en {self.tabla} - {self.fecha_operacion}"


class ConfiguracionAutomatizacion(models.Model):
    """Configuración Automatización - Tabla: contabilidad.configuracion_automatizacion"""

    id_config = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, db_column="id_empresa")
    tipo_evento = models.CharField(max_length=100)
    template_asiento = models.JSONField()
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "configuracion_automatizacion"
        managed = False
        unique_together = [["id_empresa", "tipo_evento"]]


class SiiPlanCuentasReferencia(models.Model):
    """Plan de Cuentas SII - Tabla: contabilidad.sii_plan_cuentas_referencia"""

    codigo_sii = models.CharField(max_length=20, primary_key=True)
    nombre_cuenta_sii = models.CharField(max_length=255)

    class Meta:
        db_table = "sii_plan_cuentas_referencia"
        managed = False
        ordering = ["codigo_sii"]

    def __str__(self):
        return f"{self.codigo_sii} - {self.nombre_cuenta_sii}"


class DiccionarioCuentas(models.Model):
    """Diccionario de Cuentas - Tabla: contabilidad.diccionario_cuentas"""

    id_empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, db_column="id_empresa")
    id_cuenta = models.ForeignKey(PlanCuentas, on_delete=models.CASCADE, db_column="id_cuenta")
    codigo_sii = models.ForeignKey(SiiPlanCuentasReferencia, on_delete=models.CASCADE, db_column="codigo_sii")
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "diccionario_cuentas"
        managed = False
        unique_together = [["id_empresa", "id_cuenta"]]


class CalLibrosElectronicos(models.Model):
    """CAL Libros Electrónicos - Tabla: contabilidad.cal_libros_electronicos"""

    TIPO_LIBRO_CHOICES = [
        ("DIARIO", "Diario"),
        ("MAYOR", "Mayor"),
        ("BALANCE", "Balance"),
        ("COMPRAS_VENTAS", "Compras/Ventas"),
    ]

    id_cal = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, db_column="id_empresa")
    tipo_libro = models.CharField(max_length=20, choices=TIPO_LIBRO_CHOICES)
    numero_cal = models.CharField(max_length=50)
    fecha_autorizacion = models.DateField()
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "cal_libros_electronicos"
        managed = False
        unique_together = [["id_empresa", "tipo_libro", "numero_cal"]]
        ordering = ["-fecha_autorizacion"]


class DtePendientesFirma(models.Model):
    """DTE Pendientes de Firma - Tabla: contabilidad.dte_pendientes_firma"""

    ESTADO_CHOICES = [
        ("GENERADO", "Generado"),
        ("FIRMADO", "Firmado"),
        ("ENVIADO", "Enviado"),
        ("ACEPTADO", "Aceptado"),
        ("RECHAZADO", "Rechazado"),
    ]

    id_pendiente = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_documento = models.ForeignKey(DocumentoTributario, on_delete=models.CASCADE, db_column="id_documento")
    xml_sin_firma = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="GENERADO")
    xml_firmado = models.TextField(blank=True, null=True)
    track_id_sii = models.CharField(max_length=100, blank=True, null=True)
    mensaje_error = models.TextField(blank=True, null=True)
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "dte_pendientes_firma"
        managed = False
        ordering = ["-fecha_generacion"]

    def __str__(self):
        return f"DTE {self.id_documento} - {self.estado}"


class LibrosPendientesEnvio(models.Model):
    """Libros Pendientes de Envío - Tabla: contabilidad.libros_pendientes_envio"""

    TIPO_LIBRO_CHOICES = [
        ("DIARIO", "Diario"),
        ("MAYOR", "Mayor"),
        ("BALANCE", "Balance"),
        ("COMPRAS_VENTAS", "Compras/Ventas"),
    ]

    TIPO_ENVIO_CHOICES = [
        ("MENSUAL", "Mensual"),
        ("ANUAL_OBLIGATORIO", "Anual Obligatorio"),
    ]

    ESTADO_CHOICES = [
        ("PENDIENTE_GENERAR", "Pendiente Generar"),
        ("GENERADO", "Generado"),
        ("FIRMADO", "Firmado"),
        ("ENVIADO", "Enviado"),
        ("ACEPTADO", "Aceptado"),
        ("RECHAZADO", "Rechazado"),
    ]

    id_pendiente = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, db_column="id_empresa")
    tipo_libro = models.CharField(max_length=20, choices=TIPO_LIBRO_CHOICES)
    tipo_envio = models.CharField(max_length=20, choices=TIPO_ENVIO_CHOICES)
    anio = models.IntegerField()
    mes = models.IntegerField(blank=True, null=True)
    xml_sin_firma = models.TextField(blank=True, null=True)
    xml_firmado = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="PENDIENTE_GENERAR")
    track_id_sii = models.CharField(max_length=100, blank=True, null=True)
    mensaje_error = models.TextField(blank=True, null=True)
    fecha_generacion = models.DateTimeField(blank=True, null=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "libros_pendientes_envio"
        managed = False
        ordering = ["-fecha_actualizacion"]


class CertificadoDigital(models.Model):
    """Certificado Digital - Tabla: contabilidad.certificado_digital"""

    TIPO_CHOICES = [
        ("CERTIFICADO_EMPRESA", "Certificado Empresa"),
        ("CLAVE_CAF", "Clave CAF"),
    ]

    id_certificado = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, db_column="id_empresa")
    alias = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    contenido_cifrado = models.BinaryField()
    huella_sha256 = models.CharField(max_length=64)
    fecha_carga = models.DateTimeField(auto_now_add=True)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "certificado_digital"
        managed = False
        unique_together = [["id_empresa", "alias"]]
        ordering = ["-fecha_carga"]

    def __str__(self):
        return f"{self.alias} - {self.tipo} ({self.id_empresa})"


# ============================================================================
# MODELO PERFIL - PARA SEGURIDAD Y CONTROL DE ACCESO
# ============================================================================


class Perfil(models.Model):
    """
    Perfil de usuario con relación a empresa.
    """

    ROL_CHOICES = [
        ("ADMIN", "Administrador"),
        ("CONTADOR", "Contador"),
        ("USUARIO", "Usuario"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField("auth.User", on_delete=models.CASCADE, related_name="perfil")
    empresa = models.ForeignKey(
        "core.Empresa", on_delete=models.SET_NULL, null=True, blank=True, related_name="usuarios"
    )
    rol = models.CharField(max_length=50, choices=ROL_CHOICES, default="USUARIO")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "perfil"
        managed = True

    def __str__(self):
        return f"{self.user.username} - {self.empresa.razon_social if self.empresa else 'Sin empresa'}"

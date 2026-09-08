from django.conf import settings
from django.db import models
from django.utils import timezone
import uuid


class Organizacion(models.Model):
    """Raíz del tenant (hogar u organización). Hoy hay un usuario por cuenta,
    pero toda propiedad de datos ya cuelga de acá, no del usuario directamente."""

    TIPO_CHOICES = [
        ('hogar', 'Hogar'),
        ('organizacion', 'Organización'),
    ]

    nombre = models.CharField(max_length=150)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='hogar')
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Organización'
        verbose_name_plural = 'Organizaciones'

    def __str__(self):
        return self.nombre


class Membresia(models.Model):
    """Relación usuario <-> organización (many-to-many con rol), para permitir
    que más de una persona comparta la huella de un mismo hogar/organización."""

    ROL_CHOICES = [
        ('admin', 'Administrador'),
        ('miembro', 'Miembro'),
    ]

    organizacion = models.ForeignKey(Organizacion, on_delete=models.CASCADE, related_name='miembros')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='membresias')
    rol = models.CharField(max_length=10, choices=ROL_CHOICES, default='admin')
    fecha_union = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('organizacion', 'usuario')
        verbose_name = 'Membresía'
        verbose_name_plural = 'Membresías'

    def __str__(self):
        return f'{self.usuario} @ {self.organizacion} ({self.rol})'


class RegistroBoleta(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fecha_subida = models.DateField(auto_now_add=True)
    periodo_referencia = models.CharField(max_length=64)
    archivo = models.FileField(upload_to='boletas/', blank=True, null=True)
    valor_extraido = models.JSONField(default=dict, blank=True, null=True)
    estado = models.CharField(
        max_length=16,
        choices=[
            ('Procesado', 'Procesado'),
            ('Pendiente', 'Pendiente'),
            ('Error', 'Error'),
        ],
        default='Pendiente'
    )
    procesado = models.BooleanField(default=False)
    mensaje_procesamiento = models.TextField(blank=True, null=True)
    origen = models.CharField(
        max_length=16,
        choices=[
            ('Manual', 'Manual'),
            ('Boleta', 'Boleta'),
        ],
        default='Boleta',
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='boletas',
        null=True,
        blank=True,
    )
    organizacion = models.ForeignKey(
        Organizacion,
        on_delete=models.CASCADE,
        related_name='boletas',
        null=True,
        blank=True,
    )
    creado_en = models.DateTimeField(default=timezone.now, editable=False)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'RegistroBoleta({self.periodo_referencia}, {self.estado})'


class CorreccionBoleta(models.Model):
    boleta = models.ForeignKey(RegistroBoleta, on_delete=models.CASCADE, related_name='correcciones')
    campo_modificado = models.CharField(max_length=50)
    valor_original = models.CharField(max_length=100)
    valor_corregido = models.CharField(max_length=100)
    corregido_en = models.DateTimeField(auto_now_add=True)
    corregido_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-corregido_en']

    def __str__(self):
        return f'CorreccionBoleta({self.boleta_id}, {self.campo_modificado})'


class CategoriaEmision(models.Model):
    """Catálogo cerrado de categorías de emisión (jerarquía Alcance -> Categoría, ISO 14064-1)."""

    ALCANCE_CHOICES = [
        (1, 'Alcance 1 - Directas'),
        (2, 'Alcance 2 - Energía importada'),
        (3, 'Alcance 3 - Indirectas'),
    ]

    codigo = models.SlugField(max_length=50, unique=True)
    nombre = models.CharField(max_length=120)
    alcance = models.PositiveSmallIntegerField(choices=ALCANCE_CHOICES)
    unidad_actividad = models.CharField(max_length=20, help_text='Unidad del dato de actividad, ej. kWh, litros, kg')
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ['alcance', 'codigo']
        verbose_name = 'Categoría de emisión'
        verbose_name_plural = 'Categorías de emisión'

    def __str__(self):
        return f'{self.nombre} (Alcance {self.alcance})'


class FactorEmision(models.Model):
    """Factor de emisión versionado por vigencia, con fuente citada (nunca hardcodeado en código)."""

    categoria = models.ForeignKey(CategoriaEmision, on_delete=models.PROTECT, related_name='factores')
    nombre = models.CharField(max_length=120)
    valor_kg_co2e = models.DecimalField(max_digits=12, decimal_places=6)
    unidad = models.CharField(max_length=40, help_text='ej. kg CO2e / kWh')
    fuente = models.CharField(max_length=255)
    vigente_desde = models.DateField()
    vigente_hasta = models.DateField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['categoria', '-vigente_desde']
        verbose_name = 'Factor de emisión'
        verbose_name_plural = 'Factores de emisión'

    def __str__(self):
        return f'{self.categoria.codigo} = {self.valor_kg_co2e} ({self.vigente_desde})'

    def vigente_en(self, fecha):
        if fecha < self.vigente_desde:
            return False
        if self.vigente_hasta and fecha > self.vigente_hasta:
            return False
        return True


class RegistroActividad(models.Model):
    """Dato de actividad crudo (lo que el usuario ingresa u OCR extrae), separado del cálculo."""

    ORIGEN_CHOICES = [
        ('manual', 'Manual'),
        ('ocr', 'OCR'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='registros_actividad',
    )
    organizacion = models.ForeignKey(
        Organizacion,
        on_delete=models.CASCADE,
        related_name='registros_actividad',
        null=True,
        blank=True,
    )
    categoria = models.ForeignKey(CategoriaEmision, on_delete=models.PROTECT, related_name='registros')
    periodo = models.CharField(max_length=7, help_text="Formato 'YYYY-MM'")
    cantidad = models.DecimalField(max_digits=14, decimal_places=4)
    origen = models.CharField(max_length=10, choices=ORIGEN_CHOICES, default='manual')
    # CASCADE: hoy toda actividad se origina en exactamente una boleta (OCR o manual);
    # si la boleta se borra, el dato de actividad derivado de ella no tiene razón de persistir.
    fuente_boleta = models.ForeignKey(
        RegistroBoleta,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='actividades',
    )
    creado_en = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ['-periodo', '-creado_en']
        verbose_name = 'Registro de actividad'
        verbose_name_plural = 'Registros de actividad'

    def __str__(self):
        return f'{self.categoria_id} {self.periodo} = {self.cantidad}'


class CalculoEmision(models.Model):
    """Resultado derivado: cantidad x factor vigente. Nunca se edita a mano, siempre se recalcula."""

    registro_actividad = models.OneToOneField(RegistroActividad, on_delete=models.CASCADE, related_name='calculo')
    factor = models.ForeignKey(FactorEmision, on_delete=models.PROTECT, related_name='calculos')
    resultado_kg_co2e = models.DecimalField(max_digits=14, decimal_places=4)
    calculado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cálculo de emisión'
        verbose_name_plural = 'Cálculos de emisión'

    def __str__(self):
        return f'{self.registro_actividad_id} -> {self.resultado_kg_co2e} kgCO2e'

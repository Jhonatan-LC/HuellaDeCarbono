"""Servicio de cálculo de emisiones.

Separa estrictamente dato de actividad (RegistroActividad) de factor de
emisión (FactorEmision, versionado por vigencia) de resultado (CalculoEmision,
siempre derivado, nunca editable a mano vía API).
"""
from datetime import date
from decimal import Decimal, InvalidOperation

from django.db.models import Q

from .models import CalculoEmision, CategoriaEmision, FactorEmision, RegistroActividad


def fecha_desde_periodo(periodo):
    try:
        anio, mes = periodo.split('-')
        return date(int(anio), int(mes), 1)
    except (ValueError, AttributeError, TypeError):
        return date.today()


def obtener_factor_vigente(categoria_codigo, fecha=None):
    fecha = fecha or date.today()
    return (
        FactorEmision.objects
        .filter(categoria__codigo=categoria_codigo, vigente_desde__lte=fecha)
        .filter(Q(vigente_hasta__isnull=True) | Q(vigente_hasta__gte=fecha))
        .order_by('-vigente_desde')
        .first()
    )


def calcular_y_registrar(registro_actividad):
    """(Re)calcula el CalculoEmision de un RegistroActividad con el factor vigente en su periodo."""
    fecha = fecha_desde_periodo(registro_actividad.periodo)
    factor = obtener_factor_vigente(registro_actividad.categoria.codigo, fecha)
    if factor is None:
        return None

    resultado = registro_actividad.cantidad * factor.valor_kg_co2e
    calculo, _ = CalculoEmision.objects.update_or_create(
        registro_actividad=registro_actividad,
        defaults={'factor': factor, 'resultado_kg_co2e': resultado},
    )
    return calculo


def registrar_actividad(usuario, organizacion, categoria_codigo, periodo, cantidad, origen='manual', fuente_boleta=None, ubicacion=None):
    """Crea un RegistroActividad + su CalculoEmision derivado. Retorna None si el dato no es válido."""
    try:
        cantidad_decimal = Decimal(str(cantidad))
    except (InvalidOperation, TypeError):
        return None

    if cantidad_decimal <= 0:
        return None

    categoria = CategoriaEmision.objects.filter(codigo=categoria_codigo, activa=True).first()
    if categoria is None:
        return None

    registro = RegistroActividad.objects.create(
        usuario=usuario,
        organizacion=organizacion,
        categoria=categoria,
        ubicacion=ubicacion,
        periodo=periodo,
        cantidad=cantidad_decimal,
        origen=origen,
        fuente_boleta=fuente_boleta,
    )
    calcular_y_registrar(registro)
    return registro


def resincronizar_actividades_boleta(boleta):
    """Reconstruye los RegistroActividad de una boleta desde su valor_extraido actual.

    Se usa tras una corrección manual: el dato de actividad se recrea (nunca se
    edita en el lugar) para que el CalculoEmision quede siempre trazable al
    valor vigente en boleta.valor_extraido.
    """
    boleta.actividades.all().delete()

    valor_extraido = boleta.valor_extraido or {}
    # periodo_referencia es el campo confiable ('YYYY-MM', ingresado/validado por el usuario);
    # valor_extraido['periodo'] es texto crudo de OCR y puede venir en formatos distintos.
    periodo = boleta.periodo_referencia
    origen = 'ocr' if boleta.origen == 'Boleta' else 'manual'

    # Boletas OCR (electricidad/combustible): campos fijos en la raíz de valor_extraido.
    energia = valor_extraido.get('energia_kwh')
    if energia:
        registrar_actividad(boleta.usuario, boleta.organizacion, 'electricidad', periodo, energia, origen=origen, fuente_boleta=boleta, ubicacion=boleta.ubicacion)

    combustible = valor_extraido.get('combustible_litros')
    if combustible:
        registrar_actividad(boleta.usuario, boleta.organizacion, 'combustible', periodo, combustible, origen=origen, fuente_boleta=boleta, ubicacion=boleta.ubicacion)

    # Registro manual genérico: cualquier categoría sembrada, bajo valor_extraido['actividades'].
    actividades = valor_extraido.get('actividades') or {}
    for categoria_codigo, cantidad in actividades.items():
        registrar_actividad(boleta.usuario, boleta.organizacion, categoria_codigo, periodo, cantidad, origen=origen, fuente_boleta=boleta, ubicacion=boleta.ubicacion)

import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum

from .models import CalculoEmision, RegistroActividad
from .organizaciones import organizacion_activa
from .views import CsrfExemptSessionAuthentication

logger = logging.getLogger(__name__)


class CarbonFootprintAnalyticsView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Se agrupa sobre CalculoEmision (resultado ya calculado con el factor
        # vigente en el periodo de cada RegistroActividad), no se recalcula
        # aquí con el factor de hoy sobre todo el historial.
        totales = (
            CalculoEmision.objects
            .filter(registro_actividad__organizacion=organizacion_activa(request.user))
            .values('registro_actividad__categoria__nombre')
            .annotate(total=Sum('resultado_kg_co2e'))
            .order_by('-total')
        )

        chart_data = [
            {
                "name": f"{fila['registro_actividad__categoria__nombre']} (kg CO2e)",
                "value": round(float(fila['total']), 2),
            }
            for fila in totales
        ]

        return Response(chart_data)


def get_resumen(user, ubicacion_id=None):
    """Total de emisiones y desglose por alcance GHG Protocol/ISO 14064 (1/2/3).

    Con ubicacion_id, restringe a la actividad de esa filial (ver AnalyticsOverviewView:
    lo usa el mapa de "Por planta" para filtrar toda la analítica al hacer click en un pin).
    """
    organizacion = organizacion_activa(user)

    filtro = {'registro_actividad__organizacion': organizacion}
    if ubicacion_id:
        filtro['registro_actividad__ubicacion_id'] = ubicacion_id

    total = CalculoEmision.objects.filter(**filtro).aggregate(total=Sum('resultado_kg_co2e'))['total']

    por_alcance = {1: 0.0, 2: 0.0, 3: 0.0}
    filas = (
        CalculoEmision.objects
        .filter(**filtro)
        .values('registro_actividad__categoria__alcance')
        .annotate(total=Sum('resultado_kg_co2e'))
    )
    for fila in filas:
        por_alcance[fila['registro_actividad__categoria__alcance']] = round(float(fila['total']), 2)

    return {
        "total_kg_co2e": round(float(total), 2) if total else 0.0,
        "por_alcance": por_alcance,
    }


def get_por_categoria(user, ubicacion_id=None):
    """Emisiones totales agrupadas por categoría, con su alcance (para el bar chart)."""
    filtro = {'registro_actividad__organizacion': organizacion_activa(user)}
    if ubicacion_id:
        filtro['registro_actividad__ubicacion_id'] = ubicacion_id

    totales = (
        CalculoEmision.objects
        .filter(**filtro)
        .values('registro_actividad__categoria__nombre', 'registro_actividad__categoria__alcance')
        .annotate(total=Sum('resultado_kg_co2e'))
        .order_by('-total')
    )
    return [
        {
            "categoria": fila['registro_actividad__categoria__nombre'],
            "alcance": fila['registro_actividad__categoria__alcance'],
            "valor_kg_co2e": round(float(fila['total']), 2),
        }
        for fila in totales
    ]


def get_tendencia_periodo(user, ubicacion_id=None):
    """Serie temporal de emisiones totales por periodo ('YYYY-MM'), orden ascendente."""
    filtro = {'registro_actividad__organizacion': organizacion_activa(user)}
    if ubicacion_id:
        filtro['registro_actividad__ubicacion_id'] = ubicacion_id

    totales = (
        CalculoEmision.objects
        .filter(**filtro)
        .values('registro_actividad__periodo')
        .annotate(total=Sum('resultado_kg_co2e'))
        .order_by('registro_actividad__periodo')
    )
    return [
        {
            "periodo": fila['registro_actividad__periodo'],
            "valor_kg_co2e": round(float(fila['total']), 2),
        }
        for fila in totales
    ]


def _desglose_por_prefijo(user, prefijo, ubicacion_id=None):
    """Cantidad de actividad (siempre disponible) y CO2e (null si la categoría no
    tiene aún un factor vigente citado) agrupados por categoría cuyo código empieza
    con `prefijo`. Sirve tanto para combustibles, agua y residuos."""
    organizacion = organizacion_activa(user)

    filtro_actividad = {'organizacion': organizacion, 'categoria__codigo__startswith': prefijo}
    filtro_calculo = {
        'registro_actividad__organizacion': organizacion,
        'registro_actividad__categoria__codigo__startswith': prefijo,
    }
    if ubicacion_id:
        filtro_actividad['ubicacion_id'] = ubicacion_id
        filtro_calculo['registro_actividad__ubicacion_id'] = ubicacion_id

    actividad_totales = (
        RegistroActividad.objects
        .filter(**filtro_actividad)
        .values('categoria__codigo', 'categoria__nombre', 'categoria__unidad_actividad')
        .annotate(cantidad_total=Sum('cantidad'))
        .order_by('-cantidad_total')
    )

    co2_por_codigo = dict(
        CalculoEmision.objects
        .filter(**filtro_calculo)
        .values('registro_actividad__categoria__codigo')
        .annotate(total=Sum('resultado_kg_co2e'))
        .values_list('registro_actividad__categoria__codigo', 'total')
    )

    resultado = []
    for fila in actividad_totales:
        codigo = fila['categoria__codigo']
        co2_total = co2_por_codigo.get(codigo)
        resultado.append({
            "categoria": fila['categoria__nombre'],
            "codigo": codigo,
            "unidad": fila['categoria__unidad_actividad'],
            "cantidad_total": round(float(fila['cantidad_total']), 2),
            "co2e_total": round(float(co2_total), 2) if co2_total is not None else None,
        })
    return resultado


def get_combustibles(user, ubicacion_id=None):
    return _desglose_por_prefijo(user, 'combustible', ubicacion_id)


def get_agua(user, ubicacion_id=None):
    return _desglose_por_prefijo(user, 'agua_', ubicacion_id)


def get_residuos(user, ubicacion_id=None):
    return _desglose_por_prefijo(user, 'residuos', ubicacion_id)


def get_por_planta(user, ubicacion_id=None):
    """Emisiones totales agrupadas por Ubicacion (planta/filial). Solo incluye
    actividad que sí quedó asociada a una ubicación (es un dato opcional).

    Ignora `ubicacion_id` a propósito: es la fuente de los pines del mapa, así que
    debe seguir trayendo todas las filiales aunque el resto de la analítica esté
    filtrada por una de ellas (si no, el mapa perdería el resto de los pines)."""
    totales = (
        CalculoEmision.objects
        .filter(
            registro_actividad__organizacion=organizacion_activa(user),
            registro_actividad__ubicacion__isnull=False,
        )
        .values(
            'registro_actividad__ubicacion__id',
            'registro_actividad__ubicacion__nombre',
            'registro_actividad__ubicacion__pais',
            'registro_actividad__ubicacion__latitud',
            'registro_actividad__ubicacion__longitud',
        )
        .annotate(total=Sum('resultado_kg_co2e'))
        .order_by('-total')
    )
    return [
        {
            "ubicacion_id": fila['registro_actividad__ubicacion__id'],
            "nombre": fila['registro_actividad__ubicacion__nombre'],
            "pais": fila['registro_actividad__ubicacion__pais'],
            "latitud": float(fila['registro_actividad__ubicacion__latitud'])
                if fila['registro_actividad__ubicacion__latitud'] is not None else None,
            "longitud": float(fila['registro_actividad__ubicacion__longitud'])
                if fila['registro_actividad__ubicacion__longitud'] is not None else None,
            "valor_kg_co2e": round(float(fila['total']), 2),
        }
        for fila in totales
    ]


class AnalyticsOverviewView(APIView):
    """KPIs de la sección Analítica. Cada sección se calcula de forma independiente
    y degrada a un valor vacío si falla, para no tumbar el resto del panel — mismo
    patrón de resiliencia que DashboardKPIView (ver dashboard_views.py)."""

    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]

    SECCIONES = [
        ("resumen", get_resumen, {"total_kg_co2e": 0.0, "por_alcance": {1: 0.0, 2: 0.0, 3: 0.0}}),
        ("por_categoria", get_por_categoria, []),
        ("tendencia_periodo", get_tendencia_periodo, []),
        ("combustibles", get_combustibles, []),
        ("agua", get_agua, []),
        ("residuos", get_residuos, []),
        ("por_planta", get_por_planta, []),
    ]

    def get(self, request):
        user = request.user
        ubicacion_id = request.query_params.get('ubicacion_id') or None
        data = {}

        for clave, funcion, fallback in self.SECCIONES:
            try:
                data[clave] = funcion(user, ubicacion_id)
            except Exception as e:
                logger.error(f"Error calculando '{clave}' para {user.username}: {e}", exc_info=True)
                data[clave] = fallback

        return Response(data)

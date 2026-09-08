import logging
import statistics
from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .emisiones import obtener_factor_vigente
from .models import CalculoEmision, RegistroActividad, RegistroBoleta
from .organizaciones import organizacion_activa
from .views import CsrfExemptSessionAuthentication

# Setup logger
logger = logging.getLogger(__name__)


def _valor_factor(categoria_codigo, fecha=None, default=0.0):
    """Lee el factor de emisión vigente desde FactorEmision (versionado, con fuente citada)
    en vez de un valor hardcodeado en código. Ver auditoría SKIC 2024 (27-08-2026)."""
    factor = obtener_factor_vigente(categoria_codigo, fecha)
    return float(factor.valor_kg_co2e) if factor else default


def get_gasto_mes_actual(user):
    """Calcula el gasto total del mes actual y su desglose."""
    hoy = timezone.now()
    periodo_actual = hoy.strftime('%Y-%m')

    boletas_mes_actual = RegistroBoleta.objects.filter(
        organizacion=organizacion_activa(user),
        periodo_referencia__startswith=periodo_actual
    )

    if not boletas_mes_actual.exists():
        return {"monto_clp": None, "periodo": periodo_actual, "desglose": {}}

    monto_total = 0
    desglose = {'electricidad': 0, 'combustible': 0}

    for boleta in boletas_mes_actual:
        total_boleta = boleta.valor_extraido.get('total')
        if isinstance(total_boleta, (int, float)):
            monto_total += total_boleta
            tipo = boleta.valor_extraido.get('tipo_detectado', 'desconocido')
            if tipo in desglose:
                desglose[tipo] += total_boleta
            elif tipo == 'mixto':  # Repartir el gasto si es mixto
                desglose['electricidad'] += total_boleta / 2
                desglose['combustible'] += total_boleta / 2

    return {
        "monto_clp": round(monto_total),
        "periodo": periodo_actual,
        "desglose": desglose
    }


def get_racha_meses(user):
    """Calcula la racha de meses consecutivos con al menos un dato de actividad registrado."""
    hoy = timezone.now()
    periodos_registrados = set(
        RegistroActividad.objects.filter(organizacion=organizacion_activa(user)).values_list('periodo', flat=True)
    )

    activa = hoy.strftime('%Y-%m') in periodos_registrados
    racha = 0
    mes_actual = hoy

    for _ in range(120):  # Limitar a 10 años de historial
        periodo_a_revisar = mes_actual.strftime('%Y-%m')
        if periodo_a_revisar in periodos_registrados:
            racha += 1
        else:
            break  # La racha se rompe al encontrar un mes sin dato de actividad

        primer_dia_mes = mes_actual.replace(day=1)
        mes_anterior = primer_dia_mes - timedelta(days=1)
        mes_actual = mes_anterior

    return {"cantidad": racha, "activa": activa}


def get_alerta_anomalia(user):
    """Detecta anomalías en el consumo comparando con el historial (vía RegistroActividad)."""
    hoy = timezone.now()
    periodo_actual_str = hoy.strftime('%Y-%m')
    seis_meses_atras = (hoy.replace(day=1) - timedelta(days=180)).replace(day=1)

    campo_por_categoria = {'electricidad': 'energia_kwh', 'combustible': 'combustible_litros'}
    filas = (
        RegistroActividad.objects
        .filter(
            organizacion=organizacion_activa(user),
            categoria__codigo__in=campo_por_categoria.keys(),
            periodo__gte=seis_meses_atras.strftime('%Y-%m'),
            periodo__lte=periodo_actual_str,
        )
        .values('periodo', 'categoria__codigo')
        .annotate(total=Sum('cantidad'))
    )

    consumo_mensual = {}
    for fila in filas:
        periodo = fila['periodo']
        campo = campo_por_categoria[fila['categoria__codigo']]
        consumo_mensual.setdefault(periodo, {'energia_kwh': 0, 'combustible_litros': 0})
        consumo_mensual[periodo][campo] = float(fila['total'])

    consumo_actual = consumo_mensual.pop(periodo_actual_str, None)
    historial = list(consumo_mensual.values())

    if not consumo_actual or len(historial) < 3:
        return {"detectada": False, "mensaje": "No hay suficientes datos históricos para detectar anomalías."}

    alertas = []
    for campo in ['energia_kwh', 'combustible_litros']:
        valor_actual = consumo_actual.get(campo, 0)
        valores_historial = [h[campo] for h in historial if h.get(campo, 0) > 0]

        if len(valores_historial) < 3:
            continue

        promedio = statistics.mean(valores_historial)
        if len(valores_historial) < 2: continue
        desviacion_std = statistics.stdev(valores_historial)

        umbral = promedio + 1.5 * desviacion_std

        if valor_actual > umbral and promedio > 0:
            porcentaje_desviacion = ((valor_actual - promedio) / promedio) * 100
            alertas.append({
                "detectada": True,
                "campo": campo,
                "valor_actual": round(valor_actual, 1),
                "promedio_historico": round(promedio, 1),
                "porcentaje_desviacion": round(porcentaje_desviacion, 1),
                "mensaje": f"Tu consumo de {campo.replace('_kwh', ' eléctrico').replace('_litros', ' de combustible')} este mes subió un {round(porcentaje_desviacion)}% sobre tu promedio."
            })
            
    if not alertas:
        return {"detectada": False, "mensaje": "Consumo dentro de los rangos normales."}

    return max(alertas, key=lambda a: a['porcentaje_desviacion'])


def get_comparativa_anual(user):
    """Compara la huella de CO2 del mes actual con el mismo mes del año anterior.

    Suma CalculoEmision.resultado_kg_co2e directamente (ya calculado con el
    factor vigente en el periodo de cada RegistroActividad) en vez de
    recalcular aquí con el factor de hoy.
    """
    hoy = timezone.now()
    periodo_actual_str = hoy.strftime('%Y-%m')
    año_anterior = hoy.year - 1
    periodo_anterior_str = f"{año_anterior}-{hoy.month:02d}"

    organizacion = organizacion_activa(user)

    def _co2_periodo(periodo):
        total = CalculoEmision.objects.filter(
            registro_actividad__organizacion=organizacion,
            registro_actividad__periodo=periodo,
        ).aggregate(total=Sum('resultado_kg_co2e'))['total']
        return float(total) if total else 0.0

    co2_actual = _co2_periodo(periodo_actual_str)
    co2_anterior = _co2_periodo(periodo_anterior_str)

    if co2_actual == 0 or co2_anterior == 0:
        return {"disponible": False, "mensaje": "No hay datos para comparar con el año anterior."}

    variacion = ((co2_actual - co2_anterior) / co2_anterior) * 100

    return {
        "disponible": True,
        "mes_actual_co2_kg": round(co2_actual, 2),
        "mismo_mes_año_anterior_co2_kg": round(co2_anterior, 2),
        "porcentaje_variacion": round(variacion, 1),
    }


class DashboardKPIView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        kpis = {}

        try:
            kpis["gasto_mes_actual"] = get_gasto_mes_actual(user)
        except Exception as e:
            logger.error(f"Error calculando get_gasto_mes_actual para {user.username}: {e}", exc_info=True)
            kpis["gasto_mes_actual"] = {"monto_clp": None, "periodo": "", "desglose": {}, "error": str(e)}

        try:
            kpis["racha_meses"] = get_racha_meses(user)
        except Exception as e:
            logger.error(f"Error calculando get_racha_meses para {user.username}: {e}", exc_info=True)
            kpis["racha_meses"] = {"cantidad": 0, "activa": False, "error": str(e)}

        try:
            kpis["alerta_anomalia"] = get_alerta_anomalia(user)
        except Exception as e:
            logger.error(f"Error calculando get_alerta_anomalia para {user.username}: {e}", exc_info=True)
            kpis["alerta_anomalia"] = {"detectada": False, "mensaje": "Error al calcular anomalía.", "error": str(e)}
        
        try:
            kpis["comparativa_anual"] = get_comparativa_anual(user)
        except Exception as e:
            logger.error(f"Error calculando get_comparativa_anual para {user.username}: {e}", exc_info=True)
            kpis["comparativa_anual"] = {"disponible": False, "mensaje": "Error al calcular comparativa.", "error": str(e)}

        return Response(kpis)

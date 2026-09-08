from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import migrations
from django.db.models import Q


def _fecha_desde_periodo(periodo):
    try:
        anio, mes = periodo.split('-')
        return date(int(anio), int(mes), 1)
    except (ValueError, AttributeError, TypeError):
        return date.today()


def _factor_vigente(FactorEmision, categoria, fecha):
    return (
        FactorEmision.objects
        .filter(categoria=categoria, vigente_desde__lte=fecha)
        .filter(Q(vigente_hasta__isnull=True) | Q(vigente_hasta__gte=fecha))
        .order_by('-vigente_desde')
        .first()
    )


def backfill(apps, schema_editor):
    RegistroBoleta = apps.get_model('auditoria', 'RegistroBoleta')
    CategoriaEmision = apps.get_model('auditoria', 'CategoriaEmision')
    FactorEmision = apps.get_model('auditoria', 'FactorEmision')
    RegistroActividad = apps.get_model('auditoria', 'RegistroActividad')
    CalculoEmision = apps.get_model('auditoria', 'CalculoEmision')

    try:
        cat_electricidad = CategoriaEmision.objects.get(codigo='electricidad')
        cat_combustible = CategoriaEmision.objects.get(codigo='combustible')
    except CategoriaEmision.DoesNotExist:
        return

    campos = [
        ('energia_kwh', cat_electricidad),
        ('combustible_litros', cat_combustible),
    ]

    for boleta in RegistroBoleta.objects.exclude(usuario=None):
        valor_extraido = boleta.valor_extraido or {}
        periodo = valor_extraido.get('periodo') or boleta.periodo_referencia
        origen = 'ocr' if boleta.origen == 'Boleta' else 'manual'
        fecha = _fecha_desde_periodo(periodo)

        for campo, categoria in campos:
            cantidad = valor_extraido.get(campo)
            if not cantidad:
                continue
            try:
                cantidad_decimal = Decimal(str(cantidad))
            except InvalidOperation:
                continue
            if cantidad_decimal <= 0:
                continue

            factor = _factor_vigente(FactorEmision, categoria, fecha)
            if factor is None:
                continue

            registro = RegistroActividad.objects.create(
                usuario=boleta.usuario,
                categoria=categoria,
                periodo=periodo,
                cantidad=cantidad_decimal,
                origen=origen,
                fuente_boleta=boleta,
            )
            CalculoEmision.objects.create(
                registro_actividad=registro,
                factor=factor,
                resultado_kg_co2e=cantidad_decimal * factor.valor_kg_co2e,
            )


def eliminar_backfill(apps, schema_editor):
    RegistroActividad = apps.get_model('auditoria', 'RegistroActividad')
    RegistroActividad.objects.filter(fuente_boleta__isnull=False).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('auditoria', '0006_seed_categorias_factores'),
    ]

    operations = [
        migrations.RunPython(backfill, eliminar_backfill),
    ]

from datetime import date

from django.db import migrations

FUENTE_SKIC = 'SKIC Herramienta de cálculo 2024 (Chile), hoja 4.FE'
FUENTE_RESIDUOS_DUDOSA = (
    'DUDOSO: mismo valor genérico (6.41061 kg CO2e/tonelada) repetido en 4 categorías '
    'de residuos distintas (no peligrosos, plástico, textil, papel) en la tabla de '
    'combustión de la hoja 4.FE — no parece un factor verificado por material, revisar '
    'fuente original antes de dar por definitivo.'
)

CATEGORIAS = [
    ('agua_consumo', 'Consumo de agua potable (red)', 3, 'm³'),
    ('agua_tratamiento', 'Tratamiento de aguas servidas', 3, 'm³'),
    ('transporte_aereo_corto', 'Transporte aéreo, corto alcance (≤3.700 km)', 3, 'pasajero-km'),
    ('transporte_aereo_largo', 'Transporte aéreo, largo alcance (>3.700 km)', 3, 'pasajero-km'),
    ('fugitivo_r22', 'Recarga refrigerante R-22', 1, 'kg'),
    ('fugitivo_r32', 'Recarga refrigerante R-32', 1, 'kg'),
    ('fugitivo_r125', 'Recarga refrigerante R-125', 1, 'kg'),
    ('fugitivo_r134a', 'Recarga refrigerante R-134a', 1, 'kg'),
    ('fugitivo_r407c', 'Recarga refrigerante R-407c', 1, 'kg'),
    ('fugitivo_r410a', 'Recarga refrigerante R-410a', 1, 'kg'),
    ('recarga_extintor_co2', 'Recarga de extintor CO2', 1, 'kg'),
    ('residuos_peligrosos', 'Residuos peligrosos', 3, 'kg'),
    ('residuos_aceite_mineral', 'Residuos de aceite mineral', 3, 'kg'),
    ('residuos_demolicion', 'Residuos de demolición/construcción', 3, 'kg'),
    ('residuos_madera', 'Residuos de madera (combustión)', 3, 'kg'),
    ('residuos_no_peligrosos', 'Residuos no peligrosos (mixtos)', 3, 'kg'),
    ('residuos_plastico', 'Residuos plásticos', 3, 'kg'),
    ('residuos_textil', 'Residuos textiles', 3, 'kg'),
    ('residuos_papel', 'Residuos de papel/cartón', 3, 'kg'),
    # Sin factor sembrado a propósito (celda 4.FE!C194 'Metals' vacía en el Excel origen):
    # no hay valor confiable que citar todavía. Se agrega vía admin cuando se consiga uno.
    ('residuos_metal', 'Residuos de metal/chatarra', 3, 'kg'),
]

# (categoria_codigo, nombre, valor_kg_co2e, unidad, fuente, celda)
FACTORES = [
    ('agua_consumo', 'Suministro de agua potable', '0.15311', 'kg CO2e / m³',
     'DEFRA UK 2024, Water supply', 'E139'),
    ('agua_tratamiento', 'Tratamiento de aguas servidas', '0.18574', 'kg CO2e / m³',
     'DEFRA UK 2024, Water treatment', 'E145'),
    ('transporte_aereo_corto', 'Vuelo corto alcance (DEFRA, ≤3.700 km)', '0.10974', 'kg CO2e / pasajero·km',
     'DEFRA UK 2024', 'E175'),
    ('transporte_aereo_largo', 'Vuelo largo alcance (DEFRA, >3.700 km)', '0.15423', 'kg CO2e / pasajero·km',
     'DEFRA UK 2024', 'E176'),
    ('fugitivo_r22', 'GWP-100 R-22', '1760', 'kg CO2e / kg refrigerante (GWP)',
     'IPCC AR5 2014', 'C121'),
    ('fugitivo_r32', 'GWP-100 R-32', '677', 'kg CO2e / kg refrigerante (GWP)',
     'IPCC AR5 2014', 'C122'),
    ('fugitivo_r125', 'GWP-100 R-125', '3170', 'kg CO2e / kg refrigerante (GWP)',
     'IPCC AR5 2014', 'C123'),
    ('fugitivo_r134a', 'GWP-100 R-134a', '1300', 'kg CO2e / kg refrigerante (GWP)',
     'IPCC AR5 2014', 'C124'),
    ('fugitivo_r407c', 'GWP-100 R-407c (mezcla 23% R32/25% R125/52% R134a)', '1624.21',
     'kg CO2e / kg refrigerante (GWP)', 'IPCC AR5 2014', 'C120'),
    ('fugitivo_r410a', 'GWP-100 R-410a (mezcla 50% R32/50% R125)', '1923.5',
     'kg CO2e / kg refrigerante (GWP)', 'IPCC AR5 2014', 'C125'),
    ('recarga_extintor_co2', 'Recarga de extintor de CO2 (GWP=1)', '1', 'kg CO2e / kg',
     'CO2 puro, GWP=1 por definición', 'C131'),
    ('residuos_peligrosos', 'Residuos peligrosos', '2.523', 'kg CO2e / kg',
     'ecoinvent 3.10, dataset 1789', 'D204'),
    ('residuos_aceite_mineral', 'Residuos de aceite mineral', '2.849', 'kg CO2e / kg',
     'ecoinvent 3.10, dataset 8625', 'D206'),
    ('residuos_demolicion', 'Residuos de demolición/construcción', '0.004002', 'kg CO2e / kg',
     'ecoinvent 3.10, dataset 26045', 'D207'),
    ('residuos_madera', 'Residuos de madera (combustión)', '0.021281', 'kg CO2e / kg',
     'tabla de combustión 4.FE (21.28081 kg CO2e/tonelada, convertido a kg)', 'H195'),
    ('residuos_no_peligrosos', 'Residuos no peligrosos (mixtos, combustión)', '0.006411', 'kg CO2e / kg',
     FUENTE_RESIDUOS_DUDOSA, 'H191'),
    ('residuos_plastico', 'Residuos plásticos (combustión)', '0.006411', 'kg CO2e / kg',
     FUENTE_RESIDUOS_DUDOSA, 'H197'),
    ('residuos_textil', 'Residuos textiles (combustión)', '0.006411', 'kg CO2e / kg',
     FUENTE_RESIDUOS_DUDOSA, 'G198'),
    ('residuos_papel', 'Residuos de papel/cartón (combustión)', '0.006411', 'kg CO2e / kg',
     FUENTE_RESIDUOS_DUDOSA, 'G199'),
]

VIGENTE_DESDE = date(2024, 1, 1)


def seed(apps, schema_editor):
    CategoriaEmision = apps.get_model('auditoria', 'CategoriaEmision')
    FactorEmision = apps.get_model('auditoria', 'FactorEmision')

    categorias_por_codigo = {}
    for codigo, nombre, alcance, unidad in CATEGORIAS:
        categoria, _ = CategoriaEmision.objects.get_or_create(
            codigo=codigo,
            defaults={'nombre': nombre, 'alcance': alcance, 'unidad_actividad': unidad},
        )
        categorias_por_codigo[codigo] = categoria

    for categoria_codigo, nombre, valor, unidad, fuente_original, celda in FACTORES:
        categoria = categorias_por_codigo[categoria_codigo]
        fuente = f'{fuente_original} — {FUENTE_SKIC}!{celda}'
        FactorEmision.objects.get_or_create(
            categoria=categoria,
            vigente_desde=VIGENTE_DESDE,
            defaults={
                'nombre': nombre,
                'valor_kg_co2e': valor,
                'unidad': unidad,
                'fuente': fuente,
            },
        )


def eliminar_seed(apps, schema_editor):
    CategoriaEmision = apps.get_model('auditoria', 'CategoriaEmision')
    CategoriaEmision.objects.filter(codigo__in=[c[0] for c in CATEGORIAS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('auditoria', '0010_backfill_organizacion'),
    ]

    operations = [
        migrations.RunPython(seed, eliminar_seed),
    ]

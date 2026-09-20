from datetime import date

from django.db import migrations

FUENTE_SKIC = 'SKIC Herramienta de cálculo 2024 (Chile), hoja 4.FE'

CATEGORIAS = [
    # Combustibles por tipo (alcance 1) — reemplazan en granularidad al 'combustible'
    # genérico existente, que se deja intacto por compatibilidad con datos históricos.
    ('combustible_diesel', 'Diésel (vehículos/maquinaria)', 1, 'litros'),
    ('combustible_gasolina', 'Gasolina (vehículos)', 1, 'litros'),
    ('combustible_glp', 'Gas licuado de petróleo (GLP)', 1, 'kg'),
    ('combustible_gas_natural', 'Gas natural / GNL', 1, 'm³'),
    # Agua por fuente de extracción (alcance 3) — complementa a 'agua_consumo'
    # (red pública) y 'agua_tratamiento', que ya existían.
    ('agua_superficial', 'Extracción de agua superficial/dulce', 3, 'm³'),
    ('agua_subterranea', 'Extracción de agua de napas subterráneas', 3, 'm³'),
    ('agua_mar', 'Extracción de agua de mar', 3, 'm³'),
    # Residuos por destino (alcance 3) — seguimiento de cantidad, no de cálculo de
    # emisión: no llevan factor propio, son la contraparte de las categorías de
    # residuos por material (residuos_plastico, residuos_textil, etc.) ya sembradas.
    ('residuos_reciclados', 'Residuos reciclados/reutilizados', 3, 'kg'),
    ('residuos_disposicion_final', 'Residuos enviados a disposición final', 3, 'kg'),
]

# 'combustible_diesel' reutiliza el mismo factor y fuente ya citados para el
# 'combustible' genérico (que, de hecho, siempre fue un factor de diésel) —
# ver migrations/0006_seed_categorias_factores.py.
FACTORES = [
    {
        'categoria_codigo': 'combustible_diesel',
        'nombre': 'Factor de combustión diésel',
        'valor_kg_co2e': '2.68',
        'unidad': 'kg CO2 / litro',
        'fuente': 'Factor de combustión diésel, estable en el tiempo (auditoría SKIC 2024)',
        'vigente_desde': date(2024, 1, 1),
    },
]

# Sin factor sembrado a propósito: no hay una fuente auditable a mano para extracción
# de agua por tipo de origen, gasolina/GLP/gas natural, ni para las categorías de
# residuos por destino — se completan vía admin cuando se consiga una fuente citable
# (mismo precedente que 'residuos_metal' en 0011_seed_categorias_adicionales.py).


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

    for datos in FACTORES:
        categoria = categorias_por_codigo[datos['categoria_codigo']]
        FactorEmision.objects.get_or_create(
            categoria=categoria,
            vigente_desde=datos['vigente_desde'],
            defaults={
                'nombre': datos['nombre'],
                'valor_kg_co2e': datos['valor_kg_co2e'],
                'unidad': datos['unidad'],
                'fuente': datos['fuente'],
            },
        )


def eliminar_seed(apps, schema_editor):
    CategoriaEmision = apps.get_model('auditoria', 'CategoriaEmision')
    CategoriaEmision.objects.filter(codigo__in=[c[0] for c in CATEGORIAS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('auditoria', '0013_ubicacion'),
    ]

    operations = [
        migrations.RunPython(seed, eliminar_seed),
    ]

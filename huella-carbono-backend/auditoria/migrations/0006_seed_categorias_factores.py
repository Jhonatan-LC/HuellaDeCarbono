from datetime import date

from django.db import migrations


CATEGORIAS = [
    {
        'codigo': 'electricidad',
        'nombre': 'Electricidad de red',
        'alcance': 2,
        'unidad_actividad': 'kWh',
    },
    {
        'codigo': 'combustible',
        'nombre': 'Combustión móvil (vehículo propio)',
        'alcance': 1,
        'unidad_actividad': 'litros',
    },
]

FACTORES = [
    {
        'categoria_codigo': 'electricidad',
        'nombre': 'Factor de red Chile 2024 (mix SIC/SING)',
        'valor_kg_co2e': '0.2021',
        'unidad': 'kg CO2e / kWh',
        'fuente': 'energiaabierta.cl — factor de red Chile 2024 (SIC/SING)',
        'vigente_desde': date(2024, 1, 1),
    },
    {
        'categoria_codigo': 'combustible',
        'nombre': 'Factor de combustión diésel',
        'valor_kg_co2e': '2.68',
        'unidad': 'kg CO2 / litro',
        'fuente': 'Factor de combustión diésel, estable en el tiempo (auditoría SKIC 2024)',
        'vigente_desde': date(2024, 1, 1),
    },
]


def seed_categorias_y_factores(apps, schema_editor):
    CategoriaEmision = apps.get_model('auditoria', 'CategoriaEmision')
    FactorEmision = apps.get_model('auditoria', 'FactorEmision')

    categorias_por_codigo = {}
    for datos in CATEGORIAS:
        categoria, _ = CategoriaEmision.objects.get_or_create(
            codigo=datos['codigo'],
            defaults=datos,
        )
        categorias_por_codigo[datos['codigo']] = categoria

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
    CategoriaEmision.objects.filter(codigo__in=[c['codigo'] for c in CATEGORIAS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('auditoria', '0005_categoriaemision_alter_correccionboleta_id_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_categorias_y_factores, eliminar_seed),
    ]

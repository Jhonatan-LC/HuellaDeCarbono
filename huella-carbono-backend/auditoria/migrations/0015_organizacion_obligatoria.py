import django.db.models.deletion
from django.db import migrations, models


def limpiar_boletas_huerfanas(apps, schema_editor):
    """Boletas sin usuario ni organizacion no pueden asignarse a ningún tenant real
    (organizacion_activa() necesita un usuario) — son artefactos de datos de prueba
    sin dueño, no historial de negocio real. RegistroActividad ya no tiene filas
    huérfanas (ver migración 0010_backfill_organizacion)."""
    RegistroBoleta = apps.get_model('auditoria', 'RegistroBoleta')
    RegistroBoleta.objects.filter(organizacion__isnull=True, usuario__isnull=True).delete()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('auditoria', '0014_seed_categorias_ampliadas'),
    ]

    operations = [
        migrations.RunPython(limpiar_boletas_huerfanas, noop),
        migrations.AlterField(
            model_name='registroboleta',
            name='organizacion',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='boletas', to='auditoria.organizacion'),
        ),
        migrations.AlterField(
            model_name='registroactividad',
            name='organizacion',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registros_actividad', to='auditoria.organizacion'),
        ),
    ]

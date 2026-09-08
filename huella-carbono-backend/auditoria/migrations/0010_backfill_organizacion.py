from django.db import migrations


def backfill(apps, schema_editor):
    RegistroBoleta = apps.get_model('auditoria', 'RegistroBoleta')
    RegistroActividad = apps.get_model('auditoria', 'RegistroActividad')
    Organizacion = apps.get_model('auditoria', 'Organizacion')
    Membresia = apps.get_model('auditoria', 'Membresia')

    organizacion_por_usuario = {}

    def _organizacion_de(usuario):
        if usuario is None:
            return None
        if usuario.id not in organizacion_por_usuario:
            membresia = Membresia.objects.filter(usuario=usuario).first()
            if membresia:
                organizacion = membresia.organizacion
            else:
                organizacion = Organizacion.objects.create(
                    nombre=f'Hogar de {usuario.username}',
                    tipo='hogar',
                )
                Membresia.objects.create(organizacion=organizacion, usuario=usuario, rol='admin')
            organizacion_por_usuario[usuario.id] = organizacion
        return organizacion_por_usuario[usuario.id]

    for boleta in RegistroBoleta.objects.filter(organizacion__isnull=True).exclude(usuario=None).select_related('usuario'):
        boleta.organizacion = _organizacion_de(boleta.usuario)
        boleta.save(update_fields=['organizacion'])

    for actividad in RegistroActividad.objects.filter(organizacion__isnull=True).select_related('usuario'):
        actividad.organizacion = _organizacion_de(actividad.usuario)
        actividad.save(update_fields=['organizacion'])


def eliminar_backfill(apps, schema_editor):
    # No revertimos: borrar las Organizacion creadas podría arrastrar datos
    # reales de usuario si esta migración ya lleva tiempo aplicada.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('auditoria', '0009_organizacion_registroactividad_organizacion_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill, eliminar_backfill),
    ]

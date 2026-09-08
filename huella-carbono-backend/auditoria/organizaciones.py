"""Resolución de la organización (tenant) activa de un usuario.

Hoy cada cuenta tiene exactamente un usuario, así que aquí se auto-provisiona
una Organizacion personal ('hogar') la primera vez que se necesita — nadie
tiene que crearla a mano ni migrar cuentas existentes. Si en el futuro un
usuario pertenece a más de una organización, este es el único lugar que hay
que tocar para resolver cuál es la "activa" (hoy: la primera membresía).
"""
from .models import Membresia, Organizacion


def organizacion_activa(usuario):
    membresia = Membresia.objects.filter(usuario=usuario).select_related('organizacion').first()
    if membresia:
        return membresia.organizacion

    organizacion = Organizacion.objects.create(
        nombre=f'Hogar de {usuario.get_username()}',
        tipo='hogar',
    )
    Membresia.objects.create(organizacion=organizacion, usuario=usuario, rol='admin')
    return organizacion

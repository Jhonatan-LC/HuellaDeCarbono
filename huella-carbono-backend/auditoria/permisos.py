"""Resolución y verificación del rol de un usuario dentro de su organización activa.

Hoy solo existen los roles 'admin'/'miembro' (ver Membresia.ROL_CHOICES). Este módulo
es el único punto que debe tocarse para sumar un rol más fino (editor de sitio, solo
lectura, auditor, etc.): agregar el choice en el modelo y una nueva permission class acá.
"""
from rest_framework.permissions import BasePermission

from .models import Membresia


def rol_de(usuario, organizacion):
    """Rol del usuario en esa organización, o None si no es miembro."""
    if organizacion is None:
        return None
    membresia = Membresia.objects.filter(usuario=usuario, organizacion=organizacion).first()
    return membresia.rol if membresia else None


class EsAdminDeOrganizacion(BasePermission):
    """Solo permite continuar si el usuario es 'admin' en su organización activa.

    Reservado para cambios de estructura organizacional (sitios, catálogo, membresías),
    no para el dato de consumo diario que cualquier miembro debe poder cargar.
    """
    message = 'Solo un administrador de la organización puede realizar esta acción.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        from .organizaciones import organizacion_activa

        organizacion = organizacion_activa(request.user)
        return rol_de(request.user, organizacion) == 'admin'

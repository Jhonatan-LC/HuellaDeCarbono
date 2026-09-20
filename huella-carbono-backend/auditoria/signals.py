"""Mantiene RegistroActividad/CalculoEmision sincronizados con RegistroBoleta vía signal,
sin depender de que cada vista se acuerde de llamar a resincronizar_actividades_boleta().

organizacion es obligatoria en RegistroBoleta (toda vista que la crea la fija explícita,
ver views.py) así que este signal ya no necesita rellenarla.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import RegistroBoleta


@receiver(post_save, sender=RegistroBoleta)
def sincronizar_boleta(sender, instance, **kwargs):
    if instance.usuario_id is None:
        return

    from .emisiones import resincronizar_actividades_boleta

    resincronizar_actividades_boleta(instance)

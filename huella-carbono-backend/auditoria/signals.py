"""Mantiene RegistroBoleta.organizacion y RegistroActividad/CalculoEmision
sincronizados, vía signal, sin depender de que cada vista se acuerde de hacerlo.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import RegistroBoleta


@receiver(post_save, sender=RegistroBoleta)
def sincronizar_boleta(sender, instance, **kwargs):
    if instance.usuario_id is None:
        return

    if instance.organizacion_id is None:
        from .organizaciones import organizacion_activa

        instance.organizacion = organizacion_activa(instance.usuario)
        instance.save(update_fields=['organizacion'])
        return  # el save() de arriba dispara este mismo signal otra vez, ya con organizacion seteada

    from .emisiones import resincronizar_actividades_boleta

    resincronizar_actividades_boleta(instance)

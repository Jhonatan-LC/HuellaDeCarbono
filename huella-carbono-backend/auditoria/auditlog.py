"""Único punto de escritura de RegistroAuditoria: mantiene cada call site en una línea."""
from .models import RegistroAuditoria


def registrar_auditoria(actor, accion, instancia, organizacion=None, detalle=None):
    RegistroAuditoria.objects.create(
        actor=actor if getattr(actor, 'is_authenticated', False) else None,
        organizacion=organizacion,
        accion=accion,
        modelo=type(instancia).__name__,
        objeto_id=str(instancia.pk),
        detalle=detalle or {},
    )

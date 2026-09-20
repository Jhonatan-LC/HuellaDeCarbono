from django.contrib import admin

from .auditlog import registrar_auditoria
from .models import (
    CalculoEmision,
    CategoriaEmision,
    CorreccionBoleta,
    FactorEmision,
    Membresia,
    Organizacion,
    RegistroActividad,
    RegistroAuditoria,
    RegistroBoleta,
    Ubicacion,
)


@admin.register(Organizacion)
class OrganizacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'creado_en')
    list_filter = ('tipo',)


@admin.register(Membresia)
class MembresiaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'organizacion', 'rol', 'fecha_union')
    list_filter = ('rol',)


@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'organizacion', 'pais', 'latitud', 'longitud', 'activa')
    list_filter = ('activa', 'pais')


class _AuditaCambiosDeCatalogoMixin:
    """Deja rastro en RegistroAuditoria de cambios al catálogo de factores/categorías:
    afectan los cálculos de emisión de toda la organización, así que quién los tocó y
    cuándo debe quedar trazable (ver Pendiente 'registro de auditoría' en CLAUDE.md)."""

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        registrar_auditoria(
            actor=request.user,
            accion='actualizado' if change else 'creado',
            instancia=obj,
            detalle={campo: str(valor) for campo, valor in form.cleaned_data.items()},
        )


@admin.register(CategoriaEmision)
class CategoriaEmisionAdmin(_AuditaCambiosDeCatalogoMixin, admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'alcance', 'unidad_actividad', 'activa')
    list_filter = ('alcance', 'activa')


@admin.register(FactorEmision)
class FactorEmisionAdmin(_AuditaCambiosDeCatalogoMixin, admin.ModelAdmin):
    list_display = ('categoria', 'valor_kg_co2e', 'unidad', 'fuente', 'vigente_desde', 'vigente_hasta')
    list_filter = ('categoria',)


@admin.register(RegistroActividad)
class RegistroActividadAdmin(admin.ModelAdmin):
    list_display = ('categoria', 'usuario', 'periodo', 'cantidad', 'origen', 'fuente_boleta')
    list_filter = ('categoria', 'origen')
    readonly_fields = ('id', 'creado_en')


@admin.register(CalculoEmision)
class CalculoEmisionAdmin(admin.ModelAdmin):
    list_display = ('registro_actividad', 'factor', 'resultado_kg_co2e', 'calculado_en')
    readonly_fields = ('registro_actividad', 'factor', 'resultado_kg_co2e', 'calculado_en')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    list_display = ('creado_en', 'actor', 'accion', 'modelo', 'objeto_id', 'organizacion')
    list_filter = ('accion', 'modelo')
    readonly_fields = ('actor', 'organizacion', 'accion', 'modelo', 'objeto_id', 'detalle', 'creado_en')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(RegistroBoleta)
admin.site.register(CorreccionBoleta)

from django.contrib import admin

from .models import (
    CalculoEmision,
    CategoriaEmision,
    CorreccionBoleta,
    FactorEmision,
    Membresia,
    Organizacion,
    RegistroActividad,
    RegistroBoleta,
)


@admin.register(Organizacion)
class OrganizacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'creado_en')
    list_filter = ('tipo',)


@admin.register(Membresia)
class MembresiaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'organizacion', 'rol', 'fecha_union')
    list_filter = ('rol',)


@admin.register(CategoriaEmision)
class CategoriaEmisionAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'alcance', 'unidad_actividad', 'activa')
    list_filter = ('alcance', 'activa')


@admin.register(FactorEmision)
class FactorEmisionAdmin(admin.ModelAdmin):
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


admin.site.register(RegistroBoleta)
admin.site.register(CorreccionBoleta)

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .emisiones import obtener_factor_vigente
from .models import CategoriaEmision
from .views import CsrfExemptSessionAuthentication


class CategoriasEmisionView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        categorias = CategoriaEmision.objects.filter(activa=True).order_by('alcance', 'nombre')
        return Response([
            {
                "codigo": c.codigo,
                "nombre": c.nombre,
                "alcance": c.alcance,
                "unidad_actividad": c.unidad_actividad,
                # Factor vigente hoy, para el resumen en vivo del frontend mientras el
                # usuario escribe (ver calculator.ts). Nunca se hardcodea: viene de
                # FactorEmision tal como lo usa el cálculo real (emisiones.py). Puede ser
                # null si la categoría todavía no tiene un factor citado.
                "factor_vigente_kg_co2e": self._factor_vigente(c.codigo),
            }
            for c in categorias
        ])

    def _factor_vigente(self, codigo):
        factor = obtener_factor_vigente(codigo)
        return float(factor.valor_kg_co2e) if factor else None

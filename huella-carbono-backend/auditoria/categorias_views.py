from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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
            }
            for c in categorias
        ])

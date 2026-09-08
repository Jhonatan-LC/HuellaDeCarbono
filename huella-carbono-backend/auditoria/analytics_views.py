from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum

from .models import CalculoEmision
from .organizaciones import organizacion_activa
from .views import CsrfExemptSessionAuthentication


class CarbonFootprintAnalyticsView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Se agrupa sobre CalculoEmision (resultado ya calculado con el factor
        # vigente en el periodo de cada RegistroActividad), no se recalcula
        # aquí con el factor de hoy sobre todo el historial.
        totales = (
            CalculoEmision.objects
            .filter(registro_actividad__organizacion=organizacion_activa(request.user))
            .values('registro_actividad__categoria__nombre')
            .annotate(total=Sum('resultado_kg_co2e'))
            .order_by('-total')
        )

        chart_data = [
            {
                "name": f"{fila['registro_actividad__categoria__nombre']} (kg CO2e)",
                "value": round(float(fila['total']), 2),
            }
            for fila in totales
        ]

        return Response(chart_data)

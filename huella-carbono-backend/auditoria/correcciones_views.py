from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CorreccionBoleta, RegistroBoleta
from .organizaciones import organizacion_activa
from .views import CsrfExemptSessionAuthentication


class CorregirBoletaView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        boleta = get_object_or_404(RegistroBoleta, pk=pk, organizacion=organizacion_activa(request.user))
        datos = request.data or {}

        if 'energia_kwh' in datos:
            valor_original = boleta.valor_extraido.get('energia_kwh')
            nuevo_valor = datos['energia_kwh']
            if valor_original != nuevo_valor:
                CorreccionBoleta.objects.create(
                    boleta=boleta,
                    campo_modificado='energia_kwh',
                    valor_original=str(valor_original),
                    valor_corregido=str(nuevo_valor),
                    corregido_por=request.user,
                )
            boleta.valor_extraido['energia_kwh'] = nuevo_valor

        if 'combustible_litros' in datos:
            valor_original = boleta.valor_extraido.get('combustible_litros')
            nuevo_valor = datos['combustible_litros']
            if valor_original != nuevo_valor:
                CorreccionBoleta.objects.create(
                    boleta=boleta,
                    campo_modificado='combustible_litros',
                    valor_original=str(valor_original),
                    valor_corregido=str(nuevo_valor),
                    corregido_por=request.user,
                )
            boleta.valor_extraido['combustible_litros'] = nuevo_valor

        if 'total' in datos:
            valor_original = boleta.valor_extraido.get('total')
            nuevo_valor = datos['total']
            if valor_original != nuevo_valor:
                CorreccionBoleta.objects.create(
                    boleta=boleta,
                    campo_modificado='total',
                    valor_original=str(valor_original),
                    valor_corregido=str(nuevo_valor),
                    corregido_por=request.user,
                )
            boleta.valor_extraido['total'] = nuevo_valor

        boleta.procesado = True
        boleta.estado = 'Procesado'
        boleta.save(update_fields=['valor_extraido', 'estado', 'procesado'])  # dispara sync (ver signals.py)

        return Response({
            'id': str(boleta.id),
            'valor_extraido': boleta.valor_extraido,
            'estado': boleta.estado,
            'procesado': boleta.procesado,
            'correcciones': list(boleta.correcciones.values('campo_modificado', 'valor_original', 'valor_corregido', 'corregido_en')),
        })

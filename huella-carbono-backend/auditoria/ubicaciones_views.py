from decimal import Decimal, InvalidOperation

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Ubicacion
from .organizaciones import organizacion_activa
from .permisos import EsAdminDeOrganizacion
from .views import CsrfExemptSessionAuthentication


def _serializar_ubicacion(ubicacion):
    return {
        "id": ubicacion.id,
        "nombre": ubicacion.nombre,
        "pais": ubicacion.pais,
        "latitud": float(ubicacion.latitud) if ubicacion.latitud is not None else None,
        "longitud": float(ubicacion.longitud) if ubicacion.longitud is not None else None,
    }


def _parsear_coordenada(valor):
    if valor in (None, ''):
        return None
    try:
        return Decimal(str(valor))
    except InvalidOperation:
        return None


class UbicacionesView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get_permissions(self):
        # Crear un sitio es un cambio de estructura organizacional: solo admin.
        # Consultar la lista es un dato que cualquier miembro necesita para registrar actividad.
        if self.request.method == 'POST':
            return [IsAuthenticated(), EsAdminDeOrganizacion()]
        return [IsAuthenticated()]

    def get(self, request):
        organizacion = organizacion_activa(request.user)
        ubicaciones = Ubicacion.objects.filter(organizacion=organizacion, activa=True)
        return Response([_serializar_ubicacion(u) for u in ubicaciones])

    def post(self, request):
        nombre = str(request.data.get('nombre', '')).strip()
        if not nombre:
            return Response({"detail": "El nombre de la ubicación es obligatorio."}, status=400)

        organizacion = organizacion_activa(request.user)
        ubicacion = Ubicacion.objects.create(
            organizacion=organizacion,
            nombre=nombre,
            pais=str(request.data.get('pais', '')).strip(),
            latitud=_parsear_coordenada(request.data.get('latitud')),
            longitud=_parsear_coordenada(request.data.get('longitud')),
        )

        from .auditlog import registrar_auditoria

        registrar_auditoria(
            actor=request.user,
            accion='creado',
            instancia=ubicacion,
            organizacion=organizacion,
            detalle={'nombre': ubicacion.nombre, 'pais': ubicacion.pais},
        )

        return Response(_serializar_ubicacion(ubicacion), status=201)

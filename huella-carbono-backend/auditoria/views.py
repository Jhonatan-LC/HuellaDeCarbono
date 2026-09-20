from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .extractor import extraer_valor_boleta
from .models import CategoriaEmision, RegistroBoleta, Ubicacion
from .organizaciones import organizacion_activa


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return


def _resolver_ubicacion(usuario, ubicacion_id):
    """Valida que la ubicación indicada pertenezca a la organización activa del usuario.

    Retorna None (silenciosamente) si no viene id, o si no pertenece: la ubicación es
    un dato opcional, un id inválido no debe tumbar el registro de la actividad.
    """
    if not ubicacion_id:
        return None
    return Ubicacion.objects.filter(id=ubicacion_id, organizacion=organizacion_activa(usuario)).first()


def serializar_registro(registro):
    archivo_url = registro.archivo.url if registro.archivo else None

    actividades_con_calculo = [a for a in registro.actividades.all() if hasattr(a, 'calculo')]
    co2_total = sum((a.calculo.resultado_kg_co2e for a in actividades_con_calculo), start=0)
    detalle = [
        {
            "categoria_codigo": a.categoria.codigo,
            "categoria_nombre": a.categoria.nombre,
            "alcance": a.categoria.alcance,
            "cantidad": float(a.cantidad),
            "unidad": a.categoria.unidad_actividad,
            "co2_kg": float(a.calculo.resultado_kg_co2e),
        }
        for a in actividades_con_calculo
    ]

    return {
        "id": str(registro.id),
        "archivo_url": archivo_url,
        "periodo": registro.periodo_referencia,
        "periodo_referencia": registro.periodo_referencia,
        "procesado": registro.procesado,
        "valor_extraido": registro.valor_extraido,
        "tipo_detectado": (registro.valor_extraido or {}).get('tipo_detectado', 'desconocido'),
        "mensaje_procesamiento": registro.mensaje_procesamiento,
        "creado_en": registro.creado_en.isoformat(),
        "estado": registro.estado,
        "origen": registro.origen,
        "co2_total_kg": float(co2_total),
        "actividades_detalle": detalle,
    }


class SubirBoletaView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        archivo = request.FILES.get('boleta')
        periodo = request.data.get('periodo', '').strip()
        tipo_declarado = request.data.get('tipo', '').strip().lower()

        if not archivo:
            return Response({"detail": "No se recibió ningún archivo."}, status=400)

        nombre_archivo = getattr(archivo, 'name', '').lower()
        tipo_archivo = getattr(archivo, 'content_type', '')
        formatos_permitidos = {'.pdf', '.jpg', '.jpeg', '.png'}
        if not any(nombre_archivo.endswith(ext) for ext in formatos_permitidos):
            if tipo_archivo not in {'application/pdf', 'image/jpeg', 'image/jpg', 'image/png'}:
                return Response({"detail": "Formato no soportado. Sube un PDF, JPG o PNG."}, status=400)

        if not periodo:
            return Response({"detail": "El periodo es obligatorio."}, status=400)

        ubicacion = _resolver_ubicacion(request.user, request.data.get('ubicacion_id'))

        nuevo_registro = RegistroBoleta.objects.create(
            periodo_referencia=periodo,
            archivo=archivo,
            ubicacion=ubicacion,
            estado='Pendiente',
            valor_extraido={"energia_kwh": None, "combustible_litros": None, "periodo": None},
            usuario=request.user,
            organizacion=organizacion_activa(request.user),
            origen='Boleta',
        )

        try:
            resultado_ocr = extraer_valor_boleta(nuevo_registro.archivo.path)
            valor_extraido = resultado_ocr.get('valor_extraido', {})
            if not valor_extraido.get('periodo'):
                valor_extraido['periodo'] = periodo
            if tipo_declarado in {'electricidad', 'combustible'}:
                valor_extraido['tipo_declarado'] = tipo_declarado

            nuevo_registro.valor_extraido = valor_extraido
            nuevo_registro.mensaje_procesamiento = resultado_ocr.get('mensaje', '')
            nuevo_registro.procesado = bool(resultado_ocr.get('procesado', False))
            nuevo_registro.estado = 'Procesado' if nuevo_registro.procesado else 'Error'
            nuevo_registro.save()  # dispara la sincronización a RegistroActividad/CalculoEmision (ver signals.py)
        except Exception as exc:
            nuevo_registro.procesado = False
            nuevo_registro.estado = 'Error'
            nuevo_registro.mensaje_procesamiento = str(exc)
            nuevo_registro.save()
            return Response({
                "detail": "No se pudo procesar la boleta.",
                "error": str(exc),
            }, status=400)

        return Response(serializar_registro(nuevo_registro))


class RegistrarConsumoView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        periodo = str(request.data.get('periodo', '')).strip()
        actividades_raw = request.data.get('actividades')

        if not periodo:
            return Response({"detail": "El periodo es obligatorio para guardar el registro."}, status=400)

        if not isinstance(actividades_raw, dict):
            return Response({"detail": "Debes enviar un objeto 'actividades' con al menos una categoría."}, status=400)

        codigos_validos = set(CategoriaEmision.objects.filter(activa=True).values_list('codigo', flat=True))

        actividades = {}
        for codigo, cantidad in actividades_raw.items():
            if codigo not in codigos_validos:
                return Response({"detail": f"Categoría desconocida: {codigo}."}, status=400)
            try:
                valor = float(cantidad or 0)
            except (TypeError, ValueError):
                return Response({"detail": "Los consumos deben ser números válidos."}, status=400)
            if valor > 0:
                actividades[codigo] = valor

        if not actividades:
            return Response({"detail": "Ingresa al menos un consumo mayor a cero."}, status=400)

        ubicacion = _resolver_ubicacion(request.user, request.data.get('ubicacion_id'))

        registro = RegistroBoleta.objects.create(
            periodo_referencia=periodo,
            estado='Procesado',
            procesado=True,
            origen='Manual',
            usuario=request.user,
            organizacion=organizacion_activa(request.user),
            ubicacion=ubicacion,
            valor_extraido={
                "actividades": actividades,
                "periodo": periodo,
            },
            mensaje_procesamiento='Registro ingresado manualmente.',
        )  # el signal de RegistroBoleta sincroniza RegistroActividad/CalculoEmision (ver signals.py)

        return Response(serializar_registro(registro), status=201)


class HistorialBoletasView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        registros = RegistroBoleta.objects.filter(
            organizacion=organizacion_activa(request.user)
        ).order_by('-creado_en')
        return Response({"results": [serializar_registro(registro) for registro in registros]})

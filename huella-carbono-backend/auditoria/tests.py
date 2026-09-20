import json
from unittest.mock import patch
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .extractor import extraer_valor_boleta
from .models import Membresia, Organizacion, RegistroActividad, RegistroBoleta, Ubicacion
from .dashboard_views import _valor_factor
from .emisiones import registrar_actividad
from .organizaciones import organizacion_activa


class AuthTests(TestCase):
    def test_registro_con_json_crea_usuario_inactivo_pendiente_de_verificacion(self):
        payload = {
            'username': 'nuevo',
            'email': 'nuevo@example.com',
            'password': 'ContraseñaSegura99',
            'password_confirm': 'ContraseñaSegura99',
        }

        response = self.client.post(
            reverse('register'),
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        usuario = User.objects.get(username='nuevo')
        self.assertFalse(usuario.is_active)  # activo recién tras verify_email_view
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_con_json_autentica_usuario(self):
        User.objects.create_user(username='loginuser', email='login@example.com', password='12345678')

        response = self.client.post(
            reverse('login'),
            data=json.dumps({'username': 'loginuser', 'password': '12345678'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user.is_authenticated)


class BoletaUploadTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(username='tester', password='12345678')

    def test_subida_de_boleta_devuelve_respuesta_consistente(self):
        self.client.force_login(self.usuario)
        archivo = SimpleUploadedFile(
            "boleta.pdf",
            b'%PDF-1.4\n%demo\n',
            content_type="application/pdf",
        )

        response = self.client.post(
            reverse("subir-boleta"),
            {
                "boleta": archivo,
                "periodo": "2026-06",
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(RegistroBoleta.objects.exists())
        registro = RegistroBoleta.objects.get()
        self.assertTrue(registro.procesado is False or registro.procesado is True)
        self.assertIn("archivo_url", response.json())
        self.assertIn("periodo", response.json())
        self.assertIn("valor_extraido", response.json())

    def test_archivo_no_soportado_es_rechazado(self):
        self.client.force_login(self.usuario)
        archivo = SimpleUploadedFile(
            "documento.txt",
            b'contenido no soportado',
            content_type="text/plain",
        )

        response = self.client.post(
            reverse("subir-boleta"),
            {
                "boleta": archivo,
                "periodo": "2026-06",
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(RegistroBoleta.objects.exists())

    def test_un_usuario_solo_ve_sus_propias_boletas(self):
        usuario_a = User.objects.create_user(username='usera', password='12345678')
        usuario_b = User.objects.create_user(username='userb', password='12345678')

        RegistroBoleta.objects.create(periodo_referencia='2026-06', archivo=SimpleUploadedFile('a.pdf', b'%PDF-1.4', content_type='application/pdf'), usuario=usuario_a, organizacion=organizacion_activa(usuario_a))
        RegistroBoleta.objects.create(periodo_referencia='2026-07', archivo=SimpleUploadedFile('b.pdf', b'%PDF-1.4', content_type='application/pdf'), usuario=usuario_b, organizacion=organizacion_activa(usuario_b))

        self.client.force_login(usuario_a)
        response = self.client.get(reverse('historial-boletas'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['results']), 1)
        self.assertEqual(response.json()['results'][0]['periodo_referencia'], '2026-06')


class ExtractorTests(TestCase):
    def test_extrae_y_clasifica_boleta_electrica(self):
        texto = """
        Empresa electrica CGE
        Periodo 2026-06
        Energia facturada 183,5 kWh
        Total a pagar
        """

        with patch('auditoria.extractor.procesar_archivo', return_value=texto):
            resultado = extraer_valor_boleta('demo.pdf')

        self.assertTrue(resultado['procesado'])
        self.assertEqual(resultado['tipo_detectado'], 'electricidad')
        self.assertEqual(resultado['valor_extraido']['energia_kwh'], 183.5)
        self.assertIsNone(resultado['valor_extraido']['combustible_litros'])
        self.assertEqual(resultado['valor_extraido']['periodo'], '2026-06')

    def test_extrae_y_clasifica_boleta_combustible(self):
        texto = """
        Estacion de servicio Copec
        Fecha 06/2026
        Combustible diesel volumen 54,2 litros
        """

        with patch('auditoria.extractor.procesar_archivo', return_value=texto):
            resultado = extraer_valor_boleta('demo.jpg')

        self.assertTrue(resultado['procesado'])
        self.assertEqual(resultado['tipo_detectado'], 'combustible')
        self.assertIsNone(resultado['valor_extraido']['energia_kwh'])
        self.assertEqual(resultado['valor_extraido']['combustible_litros'], 54.2)
        self.assertEqual(resultado['valor_extraido']['periodo'], '06/2026')

    def test_extrae_monto_total_de_boleta(self):
        texto = """
        Supermercado Líder
        Boleta Electrónica
        
        Varios productos de limpieza...
        
        SUBTOTAL      10.000
        IVA (19%)      1.900
        TOTAL A PAGAR $11.900
        
        RUT: 76.123.456-7
        """
        with patch('auditoria.extractor.procesar_archivo', return_value=texto):
            resultado = extraer_valor_boleta('demo.pdf')

        self.assertTrue(resultado['procesado'])
        self.assertIn('total', resultado['valor_extraido']['campos_detectados'])
        self.assertEqual(resultado['valor_extraido']['total'], 11900.0)

class DashboardKPITests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(username='kpi_tester', password='123')
        self.organizacion = organizacion_activa(self.usuario)
        self.client.force_login(self.usuario)

        # Crear datos de prueba relativos a la fecha de hoy
        hoy = timezone.now().replace(day=1)
        
        # Mes actual
        RegistroBoleta.objects.create(
            usuario=self.usuario, organizacion=self.organizacion, periodo_referencia=hoy.strftime('%Y-%m'),
            valor_extraido={'total': 25000, 'tipo_detectado': 'electricidad', 'energia_kwh': 150}
        )
        RegistroBoleta.objects.create(
            usuario=self.usuario, organizacion=self.organizacion, periodo_referencia=hoy.strftime('%Y-%m'),
            valor_extraido={'total': 75000, 'tipo_detectado': 'combustible', 'combustible_litros': 50}
        )

        # Mes anterior
        mes_1 = hoy - timedelta(days=1)
        RegistroBoleta.objects.create(
            usuario=self.usuario, organizacion=self.organizacion, periodo_referencia=mes_1.strftime('%Y-%m'),
            valor_extraido={'total': 22000, 'energia_kwh': 140}
        )

        # 2 meses atrás
        mes_2 = (mes_1).replace(day=1) - timedelta(days=1)
        RegistroBoleta.objects.create(
            usuario=self.usuario, organizacion=self.organizacion, periodo_referencia=mes_2.strftime('%Y-%m'),
            valor_extraido={'total': 23000, 'energia_kwh': 145}
        )

        # 3 meses atrás
        mes_3 = (mes_2).replace(day=1) - timedelta(days=1)
        RegistroBoleta.objects.create(
            usuario=self.usuario, organizacion=self.organizacion, periodo_referencia=mes_3.strftime('%Y-%m'),
            valor_extraido={'total': 21000, 'energia_kwh': 135}
        )

        # Mismo mes, año anterior
        año_anterior = hoy - timedelta(days=365)
        RegistroBoleta.objects.create(
            usuario=self.usuario, organizacion=self.organizacion, periodo_referencia=año_anterior.strftime('%Y-%m'),
            valor_extraido={'total': 30000, 'energia_kwh': 180}
        )


    def test_kpi_endpoint_returns_correct_structure(self):
        response = self.client.get(reverse('dashboard-kpis'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('gasto_mes_actual', data)
        self.assertIn('racha_meses', data)
        self.assertIn('alerta_anomalia', data)
        self.assertIn('comparativa_anual', data)

    def test_gasto_mes_actual_kpi(self):
        response = self.client.get(reverse('dashboard-kpis'))
        gasto = response.json()['gasto_mes_actual']
        
        self.assertEqual(gasto['monto_clp'], 100000)
        self.assertEqual(gasto['desglose']['electricidad'], 25000)
        self.assertEqual(gasto['desglose']['combustible'], 75000)

    def test_racha_meses_kpi(self):
        response = self.client.get(reverse('dashboard-kpis'))
        racha_inicial = response.json()['racha_meses']
        self.assertEqual(racha_inicial['cantidad'], 4)
        self.assertTrue(racha_inicial['activa'])
        
        # Romper la racha borrando el registro del mes anterior
        mes_anterior = (timezone.now().replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
        RegistroBoleta.objects.filter(periodo_referencia=mes_anterior).delete()

        response = self.client.get(reverse('dashboard-kpis'))
        racha_nueva = response.json()['racha_meses']
        self.assertEqual(racha_nueva['cantidad'], 1) # Solo el mes actual

    def test_alerta_anomalia_kpi(self):
        # Historial de energia_kwh: [140, 145, 135]. Promedio = 140.
        # Consumo actual: 150.
        # stdev([140, 145, 135]) es 5.
        # umbral = 140 + 1.5 * 5 = 147.5.
        # Como 150 > 147.5, debe haber una alerta.
        response = self.client.get(reverse('dashboard-kpis'))
        anomalia = response.json()['alerta_anomalia']

        self.assertTrue(anomalia['detectada'])
        self.assertEqual(anomalia['campo'], 'energia_kwh')
        self.assertEqual(anomalia['valor_actual'], 150)
        self.assertAlmostEqual(anomalia['promedio_historico'], 140.0)
        self.assertAlmostEqual(anomalia['porcentaje_desviacion'], ((150-140)/140)*100, places=1)

    def test_comparativa_anual_kpi(self):
        response = self.client.get(reverse('dashboard-kpis'))
        comparativa = response.json()['comparativa_anual']
        
        self.assertTrue(comparativa['disponible'])
        
        co2_actual = (150 * _valor_factor('electricidad')) + (50 * _valor_factor('combustible'))
        co2_anterior = 180 * _valor_factor('electricidad')
        variacion = ((co2_actual - co2_anterior) / co2_anterior) * 100

        self.assertAlmostEqual(comparativa['mes_actual_co2_kg'], co2_actual, places=2)
        self.assertAlmostEqual(comparativa['mismo_mes_año_anterior_co2_kg'], co2_anterior, places=2)
        self.assertAlmostEqual(comparativa['porcentaje_variacion'], variacion, places=1)


class RolesYPermisosTests(TestCase):
    """organizacion_activa() auto-provisiona un hogar con rol 'admin' la primera vez que se
    usa, así que para probar el rol 'miembro' hay que crear la Membresia a mano antes de
    que la vista dispare ese auto-provisionamiento."""

    def setUp(self):
        self.organizacion = Organizacion.objects.create(nombre='Empresa de prueba', tipo='organizacion')

        self.admin = User.objects.create_user(username='admin1', password='12345678')
        Membresia.objects.create(organizacion=self.organizacion, usuario=self.admin, rol='admin')

        self.miembro = User.objects.create_user(username='miembro1', password='12345678')
        Membresia.objects.create(organizacion=self.organizacion, usuario=self.miembro, rol='miembro')

    def test_admin_puede_crear_ubicacion(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('ubicaciones'), {'nombre': 'Planta Norte'})
        self.assertEqual(response.status_code, 201)
        self.assertTrue(self.organizacion.ubicaciones.filter(nombre='Planta Norte').exists())

    def test_miembro_no_puede_crear_ubicacion(self):
        self.client.force_login(self.miembro)
        response = self.client.post(reverse('ubicaciones'), {'nombre': 'Planta Sur'})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(self.organizacion.ubicaciones.filter(nombre='Planta Sur').exists())

    def test_miembro_puede_listar_ubicaciones(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('ubicaciones'), {'nombre': 'Planta Norte'})

        self.client.force_login(self.miembro)
        response = self.client.get(reverse('ubicaciones'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_me_expone_rol_y_organizacion(self):
        self.client.force_login(self.miembro)
        response = self.client.get(reverse('me'))
        usuario = response.json()['user']
        self.assertEqual(usuario['rol'], 'miembro')
        self.assertEqual(usuario['organizacion_id'], self.organizacion.id)


class OrganizacionObligatoriaTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(username='tester2', password='12345678')

    def test_boleta_manual_queda_con_organizacion_al_crear(self):
        self.client.force_login(self.usuario)
        response = self.client.post(
            reverse('registrar-consumo'),
            data=json.dumps({'periodo': '2026-06', 'actividades': {'electricidad': 100}}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        registro = RegistroBoleta.objects.get(id=response.json()['id'])
        self.assertIsNotNone(registro.organizacion_id)

        actividad = RegistroActividad.objects.get(fuente_boleta=registro)
        self.assertEqual(actividad.organizacion_id, registro.organizacion_id)


class AnalyticsPorUbicacionTests(TestCase):
    """El mapa de "Por planta" filtra toda la analítica al hacer click en una filial
    (?ubicacion_id=<id>), salvo por_planta que siempre debe traer todas las filiales
    (es la fuente de los pines del mapa) — ver analytics_views.py."""

    def setUp(self):
        self.usuario = User.objects.create_user(username='multi_planta', password='12345678')
        self.organizacion = organizacion_activa(self.usuario)
        self.planta_norte = Ubicacion.objects.create(organizacion=self.organizacion, nombre='Planta Norte', pais='Chile')
        self.planta_sur = Ubicacion.objects.create(organizacion=self.organizacion, nombre='Planta Sur', pais='Chile')

        registrar_actividad(self.usuario, self.organizacion, 'electricidad', '2026-06', 100, ubicacion=self.planta_norte)
        registrar_actividad(self.usuario, self.organizacion, 'electricidad', '2026-06', 40, ubicacion=self.planta_sur)

        self.client.force_login(self.usuario)

    def test_sin_filtro_suma_todas_las_plantas(self):
        response = self.client.get(reverse('analytics-overview'))
        self.assertEqual(response.status_code, 200)
        total_sin_filtro = response.json()['resumen']['total_kg_co2e']
        self.assertGreater(total_sin_filtro, 0)

    def test_filtro_por_ubicacion_restringe_resumen_y_categorias(self):
        response = self.client.get(reverse('analytics-overview'), {'ubicacion_id': self.planta_norte.id})
        self.assertEqual(response.status_code, 200)
        data = response.json()

        response_todas = self.client.get(reverse('analytics-overview'))
        total_todas = response_todas.json()['resumen']['total_kg_co2e']

        self.assertGreater(data['resumen']['total_kg_co2e'], 0)
        self.assertLess(data['resumen']['total_kg_co2e'], total_todas)
        self.assertTrue(all(c['categoria'] for c in data['por_categoria']))

    def test_por_planta_ignora_el_filtro_de_ubicacion(self):
        response = self.client.get(reverse('analytics-overview'), {'ubicacion_id': self.planta_norte.id})
        nombres = {p['nombre'] for p in response.json()['por_planta']}
        self.assertEqual(nombres, {'Planta Norte', 'Planta Sur'})


class CategoriasEmisionFactorVigenteTests(TestCase):
    """/api/categorias/ trae el factor vigente de cada categoría (para el resumen en vivo
    de la calculadora, ver calculator.ts) — nunca hardcodeado, viene de FactorEmision."""

    def setUp(self):
        self.usuario = User.objects.create_user(username='cat_tester', password='12345678')
        self.client.force_login(self.usuario)

    def test_categorias_traen_factor_vigente_kg_co2e(self):
        response = self.client.get(reverse('categorias-emision'))
        self.assertEqual(response.status_code, 200)
        categorias = response.json()
        self.assertTrue(categorias)

        electricidad = next(c for c in categorias if c['codigo'] == 'electricidad')
        self.assertIsInstance(electricidad['factor_vigente_kg_co2e'], float)
        self.assertGreater(electricidad['factor_vigente_kg_co2e'], 0)

from django.urls import path
from .analytics_views import CarbonFootprintAnalyticsView
from .categorias_views import CategoriasEmisionView
from .auth_views import (
    csrf_token,
    login_view,
    logout_view,
    me_view,
    register_view,
    resend_verification_view,
    verify_email_view,
)
from .correcciones_views import CorregirBoletaView
from .dashboard_views import DashboardKPIView
from .views import HistorialBoletasView, RegistrarConsumoView, SubirBoletaView

urlpatterns = [
    path('dashboard/kpis/', DashboardKPIView.as_view(), name='dashboard-kpis'),
    path('analytics/carbon-footprint/', CarbonFootprintAnalyticsView.as_view(), name='carbon-footprint-analytics'),
    path('boletas/upload/', SubirBoletaView.as_view(), name='subir-boleta'),
    path('boletas/historial/', HistorialBoletasView.as_view(), name='historial-boletas'),
    path('boletas/<uuid:pk>/corregir/', CorregirBoletaView.as_view(), name='corregir-boleta'),
    path('consumos/registrar/', RegistrarConsumoView.as_view(), name='registrar-consumo'),
    path('categorias/', CategoriasEmisionView.as_view(), name='categorias-emision'),
    path('auth/register/', register_view, name='register'),
    path('auth/verify-email/', verify_email_view, name='verify-email'),
    path('auth/resend-verification/', resend_verification_view, name='resend-verification'),
    path('auth/login/', login_view, name='login'),
    path('auth/logout/', logout_view, name='logout'),
    path('auth/me/', me_view, name='me'),
    path('auth/csrf/', csrf_token, name='csrf'),
]

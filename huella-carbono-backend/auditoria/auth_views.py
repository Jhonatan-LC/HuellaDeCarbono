import json

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt


@ensure_csrf_cookie
def csrf_token(request):
    return JsonResponse({"detail": "CSRF cookie set"})


def _get_payload(request):
    if request.content_type and 'application/json' in request.content_type:
        try:
            return json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return {}
    return request.POST


@require_POST
@csrf_exempt
def register_view(request):
    payload = _get_payload(request)
    username = str(payload.get('username', '')).strip() if isinstance(payload, dict) else ''
    email = str(payload.get('email', '')).strip() if isinstance(payload, dict) else ''
    password = str(payload.get('password', '')) if isinstance(payload, dict) else ''

    if not username or not email or not password:
        return JsonResponse({"detail": "Todos los campos son obligatorios."}, status=400)

    if User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists():
        return JsonResponse({"detail": "Usuario o email ya registrados."}, status=400)

    user = User.objects.create_user(username=username, email=email, password=password)
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)
    return JsonResponse({"user": {"id": user.id, "username": user.username, "email": user.email}})


@require_POST
@csrf_exempt
def login_view(request):
    payload = _get_payload(request)
    username = str(payload.get('username', '')).strip() if isinstance(payload, dict) else ''
    password = str(payload.get('password', '')) if isinstance(payload, dict) else ''

    user = authenticate(request, username=username, password=password)
    if not user:
        return JsonResponse({"detail": "Credenciales inválidas."}, status=400)

    login(request, user)
    return JsonResponse({"user": {"id": user.id, "username": user.username, "email": user.email}})


@require_POST
def logout_view(request):
    logout(request)
    return JsonResponse({"detail": "Sesión cerrada"})


def me_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "No autenticado"}, status=401)

    return JsonResponse({"user": {"id": request.user.id, "username": request.user.username, "email": request.user.email}})

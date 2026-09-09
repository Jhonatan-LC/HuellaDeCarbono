import json
import secrets

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .models import CodigoVerificacionEmail


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


def _enviar_codigo_verificacion(user):
    CodigoVerificacionEmail.objects.filter(usuario=user, usado=False).update(usado=True)
    codigo = f'{secrets.randbelow(1_000_000):06d}'
    expira_en = timezone.now() + timezone.timedelta(minutes=settings.VERIFICATION_CODE_TTL_MINUTES)
    CodigoVerificacionEmail.objects.create(usuario=user, codigo=codigo, expira_en=expira_en)
    send_mail(
        subject='Tu código de verificación - Huella de Carbono',
        message=(
            f'Hola {user.username},\n\n'
            f'Tu código de verificación es: {codigo}\n'
            f'Vence en {settings.VERIFICATION_CODE_TTL_MINUTES} minutos.'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


@require_POST
def register_view(request):
    payload = _get_payload(request)
    username = str(payload.get('username', '')).strip() if isinstance(payload, dict) else ''
    email = str(payload.get('email', '')).strip() if isinstance(payload, dict) else ''
    password = str(payload.get('password', '')) if isinstance(payload, dict) else ''
    password_confirm = str(payload.get('password_confirm', '')) if isinstance(payload, dict) else ''

    if not username or not email or not password:
        return JsonResponse({"detail": "Todos los campos son obligatorios."}, status=400)

    if password != password_confirm:
        return JsonResponse({"detail": "Las contraseñas no coinciden."}, status=400)

    if User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists():
        return JsonResponse({"detail": "Usuario o email ya registrados."}, status=400)

    try:
        validate_password(password)
    except ValidationError as exc:
        return JsonResponse({"detail": " ".join(exc.messages)}, status=400)

    user = User.objects.create_user(username=username, email=email, password=password)
    user.is_active = False
    user.save(update_fields=['is_active'])

    try:
        _enviar_codigo_verificacion(user)
    except Exception:
        user.delete()
        return JsonResponse(
            {"detail": "No se pudo enviar el correo de verificación. Intenta nuevamente."}, status=502
        )

    return JsonResponse({"detail": "Cuenta creada. Revisa tu correo para el código de verificación.", "username": user.username})


@require_POST
def verify_email_view(request):
    payload = _get_payload(request)
    username = str(payload.get('username', '')).strip() if isinstance(payload, dict) else ''
    codigo = str(payload.get('codigo', '')).strip() if isinstance(payload, dict) else ''

    if not username or not codigo:
        return JsonResponse({"detail": "Usuario y código son obligatorios."}, status=400)

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({"detail": "Código inválido o vencido."}, status=400)

    entrada = CodigoVerificacionEmail.objects.filter(usuario=user, codigo=codigo, usado=False).order_by('-creado_en').first()
    if not entrada or not entrada.vigente():
        return JsonResponse({"detail": "Código inválido o vencido."}, status=400)

    entrada.usado = True
    entrada.save(update_fields=['usado'])

    user.is_active = True
    user.save(update_fields=['is_active'])

    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)
    return JsonResponse({"user": {"id": user.id, "username": user.username, "email": user.email}})


@require_POST
def resend_verification_view(request):
    payload = _get_payload(request)
    username = str(payload.get('username', '')).strip() if isinstance(payload, dict) else ''

    try:
        user = User.objects.get(username=username, is_active=False)
    except User.DoesNotExist:
        # No revelamos si el usuario existe o ya está verificado.
        return JsonResponse({"detail": "Si la cuenta existe y no está verificada, enviamos un nuevo código."})

    _enviar_codigo_verificacion(user)
    return JsonResponse({"detail": "Si la cuenta existe y no está verificada, enviamos un nuevo código."})


@require_POST
def login_view(request):
    payload = _get_payload(request)
    username = str(payload.get('username', '')).strip() if isinstance(payload, dict) else ''
    password = str(payload.get('password', '')) if isinstance(payload, dict) else ''

    login_username = username
    if '@' in username:
        candidato_email = User.objects.filter(email__iexact=username).first()
        if candidato_email:
            login_username = candidato_email.username

    user = authenticate(request, username=login_username, password=password)
    if not user:
        candidato = User.objects.filter(username=login_username).first()
        if candidato and not candidato.is_active and candidato.check_password(password):
            return JsonResponse(
                {"detail": "Debes verificar tu correo antes de iniciar sesión.", "requires_verification": True},
                status=403,
            )
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

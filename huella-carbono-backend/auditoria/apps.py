from django.apps import AppConfig


class AuditoriaConfig(AppConfig):
    name = 'auditoria'

    def ready(self):
        from . import signals  # noqa: F401

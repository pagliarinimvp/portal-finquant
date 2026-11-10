from django.apps import AppConfig


class ContasConfig(AppConfig):
    name = 'contas'

    def ready(self):
        # Registra os sinais do limite de tentativas de login.
        from . import limite_login  # noqa: F401

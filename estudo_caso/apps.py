import os
import sys

from django.apps import AppConfig


class EstudoCasoConfig(AppConfig):
    name = 'estudo_caso'
    verbose_name = 'Análise de ações'

    def ready(self):
        # No servidor (gunicorn), carrega o núcleo, o pandas, o scipy e o plotly antes da primeira visita (~10 s no
        # Render). Tem de ser aqui, na mesma thread, enquanto o processo ainda não aceita requisições: numa thread à
        # parte, o import concorria com o de uma requisição e travava (`_DeadlockError` em `config.urls`, 09/11/2026),
        # deixando o site inteiro com erro 500. Nada de views nem urls aqui: só os módulos de cálculo e de telas.
        if "gunicorn" in os.path.basename(sys.argv[0]):
            from . import telas  # noqa: F401
            from .quant import servico  # noqa: F401

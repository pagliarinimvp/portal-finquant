import os
import sys
import threading

from django.apps import AppConfig


def _carregar():
    """Importa o núcleo, o pandas, o scipy e o plotly antes da primeira visita (no Render, ~10 s)."""
    from . import telas, views  # noqa: F401


class EstudoCasoConfig(AppConfig):
    name = 'estudo_caso'
    verbose_name = 'Análise de ações'

    def ready(self):
        # Só no servidor de verdade (gunicorn). Em `manage.py migrate`, `test` etc., não vale a pena esperar.
        if "gunicorn" in os.path.basename(sys.argv[0]):
            threading.Thread(target=_carregar, daemon=True, name="carregar-estudo-caso").start()

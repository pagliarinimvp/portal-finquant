import os
import sys
import threading

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
            from django.core.cache import caches
            from django.core.cache.backends import db  # noqa: F401 — o backend do cache, importado aqui e não na thread

            from . import execucao, telas, vigia  # noqa: F401
            from .quant import servico  # noqa: F401

            caches["analises"]  # noqa: B018 — instancia o backend agora (sem consultar o banco)
            # Pré-cálculo de madrugada (`execucao.janela()`, `ESTUDO_JANELA` no settings; vazio = desligado): tudo o que
            # a thread usa já foi importado acima, e ela espera `execucao.PAUSA_INICIAL` e a janela antes de trabalhar.
            threading.Thread(target=execucao.precalcular_ocioso, daemon=True, name="precalculo-ocioso").start()
            vigia.iniciar()

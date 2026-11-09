"""Calcula e guarda as configurações mais visitadas, para que abram na hora.

Roda no build do Render, depois do `atualizar_dados_estudo`: a configuração padrão do formulário (PETR4) e a seleção
automática com os mesmos padrões. Falha não quebra o build: a análise só deixa de abrir na hora.
"""
from django.core.management.base import BaseCommand

from estudo_caso import execucao
from estudo_caso.forms import PADROES


def configuracoes() -> list[dict]:
    base = {k: v for k, v in PADROES.items()}
    return [base, {**base, "selecao": "automatica", "tickers": []}]


class Command(BaseCommand):
    help = "Calcula e guarda no cache as configurações padrão da análise de ações."

    def handle(self, *args, **options):
        for cfg in configuracoes():
            nome = "seleção automática" if cfg["selecao"] == "automatica" else ", ".join(cfg["tickers"])
            k = execucao.chave(cfg)
            if execucao.resultado(k) is not None:
                self.stdout.write(f"Já guardada: {nome}.")
                continue
            try:
                execucao.rodar_agora(cfg, k)
            except Exception as e:      # noqa: BLE001
                self.stderr.write(self.style.WARNING(f"Não foi possível pré-calcular {nome}: {e}"))
                continue
            self.stdout.write(self.style.SUCCESS(f"Guardada: {nome}."))

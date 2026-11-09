"""Baixa os preços das ações do Ibovespa, o Ibovespa e a Selic para `estudo_caso/dados/`.

Roda no build do Render (toda semana, pelo deploy automático). As requisições nunca baixam nada: leem só esses CSVs.
Se o Yahoo ou o Banco Central falharem, os CSVs que estão no git continuam valendo e o build não quebra.
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from estudo_caso.quant import config, dados, universo


class Command(BaseCommand):
    help = "Atualiza os CSVs de preços, Ibovespa e Selic usados pela análise de ações."

    def handle(self, *args, **options):
        pasta = settings.DADOS_ESTUDO
        try:
            falhas = dados.atualizar_cache(sorted(universo.IBOVESPA), config.inicio_historico(), pasta)
        except Exception as e:      # noqa: BLE001 — sem rede ou fonte fora do ar: segue com os CSVs do git
            self.stderr.write(self.style.WARNING(f"Não foi possível atualizar os dados ({e}). Seguem os CSVs que já estão no repositório."))
            return
        for f in falhas:
            self.stderr.write(self.style.WARNING(f"Falha: {f}"))
        self.stdout.write(self.style.SUCCESS(f"Dados atualizados em {pasta} ({len(falhas)} falha(s))."))

"""Referências do Brasil: Selic (Banco Central, SGS 11) e Ibovespa (Yahoo Finance, ^BVSP).

Viram retornos diários alinhados às datas da análise.
"""
import pandas as pd

from . import universo
from .dados import SGS_SELIC_DIARIA, CsvFonte, DadosIndisponiveis

ROTULOS = {"selic": "Selic", "ibov": "Ibovespa"}
FOLGA_COBERTURA = pd.Timedelta(days=10)      # feriados e o atraso de publicação da taxa não contam como falta


def _nota_cobertura(nome: str, serie: pd.Series, indice: pd.DatetimeIndex) -> str | None:
    """Referência que não cobre o período rende zero nos dias sem dado: isso favorece a regra, então a página avisa."""
    if serie.empty:
        return f"{ROTULOS[nome]} sem dados no período analisado: ela aparece sem render."
    ini, fim = serie.index.min(), serie.index.max()
    if ini <= indice[0] + FOLGA_COBERTURA and fim >= indice[-1] - FOLGA_COBERTURA:
        return None
    return (f"Os dados de {ROTULOS[nome]} disponíveis vão de {ini.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}, e a análise vai de "
            f"{indice[0].strftime('%d/%m/%Y')} a {indice[-1].strftime('%d/%m/%Y')}. Nos dias sem dado, ela aparece sem render, "
            "o que distorce a comparação. Rode de novo com internet para atualizar.")


def _acumular_taxa_diaria(taxa_pct: pd.Series, indice: pd.DatetimeIndex) -> pd.Series:
    """Taxa % ao dia (SGS) -> retorno composto entre as datas do índice (inclui dias sem pregão)."""
    nivel = (1.0 + taxa_pct / 100.0).cumprod()
    uniao = nivel.index.union(indice)
    nivel = nivel.reindex(uniao).ffill().reindex(indice)
    return nivel.pct_change().fillna(0.0)


def carregar(fonte: CsvFonte, nomes: list[str], indice: pd.DatetimeIndex):
    """Devolve ({nome: retornos alinhados a `indice`}, notas)."""
    fim = indice[-1].strftime("%Y-%m-%d")
    # pega um pouco antes para o retorno da primeira data do índice
    ini_ext = (indice[0] - pd.Timedelta(days=45)).strftime("%Y-%m-%d")
    series, notas = {}, []
    for nome in nomes:
        try:
            if nome == "selic":
                s = fonte.serie_sgs(SGS_SELIC_DIARIA, ini_ext, fim)
                series[nome] = _acumular_taxa_diaria(s, indice)
                notas.append(_nota_cobertura(nome, s, indice))
            elif nome == "ibov":
                p = fonte.precos(universo.SIMBOLO_IBOV, ini_ext, fim)["Close"]
                notas.append(_nota_cobertura(nome, p, indice))
                p = p.reindex(p.index.union(indice)).ffill().reindex(indice)
                series[nome] = p.pct_change().fillna(0.0)
        except DadosIndisponiveis as e:
            notas.append(f"Referência {ROTULOS.get(nome, nome)} indisponível: {e}")
    return series, [n for n in notas if n]

"""Fixtures: dados sintéticos gravados no formato do cache (rodam sem rede e sem Django)."""
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quant.dados import CsvFonte  # noqa: E402

TICKERS = ["PETR4", "VALE3", "ITUB4", "BBDC4", "ABEV3", "WEGE3", "RENT3", "SUZB3", "GGBR4", "LREN3",
           "B3SA3", "BBAS3"]
N_PREGOES = 1500


def inicio_sintetico(n=N_PREGOES) -> str:
    """Início para `n` pregões terminarem hoje, sempre dentro da janela de 10 anos da análise."""
    return pd.bdate_range(end=pd.Timestamp(date.today()), periods=n)[0].strftime("%Y-%m-%d")


def serie_ohlc(n=1500, semente=0, mu=0.0004, sigma=0.015, inicio="2018-01-01", preco0=30.0):
    rng = np.random.default_rng(semente)
    datas = pd.bdate_range(inicio, periods=n)
    ret = rng.normal(mu, sigma, n)
    fech = preco0 * np.cumprod(1 + ret)
    abre = np.concatenate([[preco0], fech[:-1]]) * (1 + rng.normal(0, 0.002, n))
    alta = np.maximum(abre, fech) * (1 + np.abs(rng.normal(0, 0.005, n)))
    baixa = np.minimum(abre, fech) * (1 - np.abs(rng.normal(0, 0.005, n)))
    return pd.DataFrame({"Open": abre, "High": alta, "Low": baixa, "Close": fech,
                         "Volume": rng.integers(100_000, 1_000_000, n)}, index=datas)


def grava_preco(pasta: Path, simbolo: str, df: pd.DataFrame):
    seguro = simbolo.replace("^", "idx_").replace("=", "_").replace(".", "_")
    df.to_csv(pasta / f"preco_{seguro}.csv")


def gravar_cache(pasta: Path, n=N_PREGOES):
    inicio = inicio_sintetico(n)
    for k, t in enumerate(TICKERS):
        grava_preco(pasta, f"{t}.SA", serie_ohlc(n, semente=k, mu=0.0003 + 0.0001 * (k % 4), inicio=inicio))
    grava_preco(pasta, "^BVSP", serie_ohlc(n, 100, 0.0003, 0.012, inicio, 80000))
    datas = pd.bdate_range(pd.Timestamp(inicio) - pd.Timedelta(days=40), periods=n + 40)
    pd.DataFrame({"valor": 0.045}, index=datas).rename_axis("data").to_csv(pasta / "sgs_11.csv")


@pytest.fixture(scope="session")
def pasta_sintetica(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("cache")
    gravar_cache(pasta)
    return pasta


@pytest.fixture
def fonte(pasta_sintetica):
    return CsvFonte(pasta_sintetica)

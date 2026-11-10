"""Fontes de dados e a alternativa quando o SGS está fora do ar. Sem rede."""
import pandas as pd
import pytest

from quant import dados
from quant.dados import CsvFonte, DadosIndisponiveis, YFinanceFonte, selic_aproximada
from conftest import serie_ohlc


# ------------------------------------------------------------------ Selic aproximada pela meta Selic
def test_selic_aproximada_segue_a_meta_vigente():
    meta = pd.DataFrame({"meta": [12.0, 11.0]}, index=pd.to_datetime(["2024-01-02", "2024-03-01"]))
    dias = pd.to_datetime(["2024-02-01", "2024-02-29", "2024-03-01", "2024-04-01"])
    v = selic_aproximada(meta, dias)["valor"]
    antes = ((1 + (12.0 - 0.10) / 100) ** (1 / 252) - 1) * 100
    depois = ((1 + (11.0 - 0.10) / 100) ** (1 / 252) - 1) * 100
    assert v.iloc[0] == pytest.approx(antes) and v.iloc[1] == pytest.approx(antes)
    assert v.iloc[2] == pytest.approx(depois) and v.iloc[3] == pytest.approx(depois)
    # 252 pregões compostos devolvem a taxa anual da meta menos o spread
    assert (1 + antes / 100) ** 252 - 1 == pytest.approx(0.119)


# ------------------------------------------------------------------ cadeia de alternativas
META = pd.DataFrame({"meta": [14.25, 14.0]}, index=pd.to_datetime(["2025-06-19", "2025-08-01"])).rename_axis("Date")


@pytest.fixture
def pasta_com_ibov(tmp_path):
    ibov = serie_ohlc(300, 7, inicio="2025-03-03", preco0=130000)
    ibov.to_csv(tmp_path / "preco_idx_BVSP.csv")             # recém-criado => "fresco" para o YFinanceFonte
    return tmp_path


def test_cache_offline_aproxima_selic(pasta_com_ibov):
    META.to_csv(pasta_com_ibov / "copom_meta_selic.csv")
    f = CsvFonte(pasta_com_ibov)
    selic = f.serie_sgs(dados.SGS_SELIC_DIARIA, "2025-07-01", "2025-08-29")
    assert len(selic) > 30 and selic.between(0.04, 0.06).all()    # ~0,05% ao dia com Selic ~14%
    assert any("APROXIMADA" in a for a in f.avisos)


def test_sem_cache_nem_alternativa_levanta(tmp_path):
    with pytest.raises(DadosIndisponiveis):
        CsvFonte(tmp_path).serie_sgs(dados.SGS_SELIC_DIARIA, "2025-01-01", "2025-02-01")


def test_sgs_fora_do_ar_usa_alternativa_e_grava_cache(pasta_com_ibov, monkeypatch):
    def sgs_fora(codigo, inicio):
        raise ConnectionError("api.bcb.gov.br não resolve")

    monkeypatch.setattr(YFinanceFonte, "_baixar_sgs", staticmethod(sgs_fora))
    monkeypatch.setattr(YFinanceFonte, "_baixar_meta_selic", staticmethod(lambda: META))
    f = YFinanceFonte(pasta_com_ibov)
    selic = f.serie_sgs(dados.SGS_SELIC_DIARIA, "2025-07-01", "2025-08-29")
    assert len(selic) > 30
    assert f.avisos.count([a for a in f.avisos if "APROXIMADA" in a][0]) == 1       # aviso sem repetição
    # a meta ficou no cache: o modo offline passa a funcionar sozinho
    offline = CsvFonte(pasta_com_ibov)
    assert len(offline.serie_sgs(dados.SGS_SELIC_DIARIA, "2025-07-01", "2025-08-29")) == len(selic)


def test_tudo_fora_do_ar_da_mensagem_clara(tmp_path, monkeypatch):
    def fora(*a, **k):
        raise ConnectionError("sem rede")

    monkeypatch.setattr(YFinanceFonte, "_baixar_sgs", staticmethod(fora))
    monkeypatch.setattr(YFinanceFonte, "_baixar_meta_selic", staticmethod(fora))
    with pytest.raises(DadosIndisponiveis, match="fonte alternativa também falhou"):
        YFinanceFonte(tmp_path).serie_sgs(dados.SGS_SELIC_DIARIA, "2025-01-01", "2025-02-01")


# ------------------------------------------------------------------ leitura do formato real
class Resp:
    def __init__(self, dado):
        self.dado = dado

    def raise_for_status(self): ...

    def json(self):
        return self.dado


def test_parse_copom(monkeypatch):
    import requests
    conteudo = [
        {"DataInicioVigencia": "2026-09-17T03:00:00Z", "MetaSelic": 13.75},
        {"DataInicioVigencia": "2026-08-06T03:00:00Z", "MetaSelic": 14.0},
        {"DataInicioVigencia": "2026-01-01T03:00:00Z", "MetaSelic": None},          # sem meta: ignorada
        {"DataInicioVigencia": "1996-07-01T03:00:00Z", "MetaSelic": 1.9},           # meta mensal antiga: ignorada
    ]
    monkeypatch.setattr(requests, "get", lambda *a, **k: Resp({"conteudo": conteudo}))
    df = YFinanceFonte._baixar_meta_selic()
    assert list(df["meta"]) == [14.0, 13.75] and df.index[0] == pd.Timestamp("2026-08-06")


def test_janela_de_10_anos():
    from datetime import date

    from quant.config import inicio_historico
    assert inicio_historico(date(2026, 11, 6)) == "2016-11-06"
    assert inicio_historico(date(2028, 2, 29)) == "2018-02-28"          # 29/02 não existe no ano de destino


def test_nome_do_arquivo_de_cache(tmp_path):
    assert CsvFonte(tmp_path)._arq_preco("PETR4.SA").name == "preco_PETR4_SA.csv"


# ------------------------------------------------------------------ referência que não cobre o período
def test_selic_que_nao_cobre_o_periodo_gera_aviso(tmp_path):
    from quant import benchmarks as bm
    indice = pd.bdate_range("2020-01-01", periods=500)
    pd.DataFrame({"valor": 0.04}, index=indice[200:300]).rename_axis("data").to_csv(tmp_path / "sgs_11.csv")
    series, notas = bm.carregar(CsvFonte(tmp_path), ["selic"], indice)
    assert len(notas) == 1 and "sem render" in notas[0]
    assert indice[200].strftime("%d/%m/%Y") in notas[0]                 # datas no padrão brasileiro
    assert series["selic"].iloc[:200].eq(0).all()                       # é justamente o efeito de que o aviso trata


def test_selic_completa_nao_gera_aviso(tmp_path):
    from quant import benchmarks as bm
    indice = pd.bdate_range("2020-01-01", periods=500)
    pd.DataFrame({"valor": 0.04}, index=pd.bdate_range("2019-11-20", "2022-01-01")).rename_axis("data").to_csv(tmp_path / "sgs_11.csv")
    assert bm.carregar(CsvFonte(tmp_path), ["selic"], indice)[1] == []


def test_falha_no_download_com_cache_avisa(pasta_com_ibov, monkeypatch):
    def fora(*a, **k):
        raise ConnectionError("sem rede")

    pd.DataFrame({"valor": 0.04}, index=pd.bdate_range("2025-01-01", periods=100)).rename_axis("data").to_csv(pasta_com_ibov / "sgs_11.csv")
    monkeypatch.setattr(YFinanceFonte, "_baixar_sgs", staticmethod(fora))
    monkeypatch.setattr(YFinanceFonte, "_baixar_preco", staticmethod(fora))
    f = YFinanceFonte(pasta_com_ibov, validade_horas=0)
    f.serie_sgs(dados.SGS_SELIC_DIARIA, "2025-01-01", "2025-03-01")
    serie_ohlc(300, 1, inicio="2025-01-01").to_csv(pasta_com_ibov / "preco_PETR4_SA.csv")
    f.precos("PETR4", "2025-01-01", "2025-03-01")
    assert any("atualizar a Selic" in a for a in f.avisos) and any("atualizar PETR4" in a for a in f.avisos)


# ------------------------------------------------------------------ preço da bolsa × preço ajustado
def test_fator_bolsa_desfaz_desdobramento_e_dividendo():
    """Um desdobramento de 1 para 2 no 3º dia dobra os preços anteriores; o dividendo vem da razão com o ajustado."""
    dias = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"])
    bruto = pd.DataFrame({"Close": [10.0, 10.0, 10.0, 10.0], "Stock Splits": [0.0, 0.0, 2.0, 0.0]}, index=dias)   # já corrigido pelo desdobramento
    ajustado = pd.Series([8.0, 8.0, 10.0, 10.0], index=dias)                                                        # dividendo depois do 2º dia
    f = dados._fator_bolsa(bruto, ajustado)
    assert list(f) == [2.5, 2.5, 1.0, 1.0]           # 10 × 2 (desdobramento) ÷ 8 (dividendo) = 2,5


def test_cache_sem_fator_continua_funcionando(tmp_path):
    """Cache antigo, sem a coluna: os preços saem iguais, e o fator é None. Com a coluna, os preços não a trazem."""
    df = serie_ohlc(300)
    df.to_csv(tmp_path / "preco_PETR4_SA.csv")
    fonte = CsvFonte(tmp_path)
    assert fonte.fator_bolsa("PETR4") is None
    df.assign(FatorBolsa=4.0).to_csv(tmp_path / "preco_PETR4_SA.csv")
    p = fonte.precos("PETR4", str(df.index[0].date()), str(df.index[-1].date()))
    assert list(p.columns) == dados.COLUNAS_OHLCV
    assert (fonte.fator_bolsa("PETR4") == 4.0).all()


def test_preco_da_bolsa_chega_ao_exemplo_e_as_operacoes(pasta_sintetica, tmp_path):
    import shutil

    from quant import servico
    pasta = tmp_path / "cache"
    shutil.copytree(pasta_sintetica, pasta)
    arq = pasta / "preco_PETR4_SA.csv"
    pd.read_csv(arq, index_col=0).assign(FatorBolsa=4.0).to_csv(arq)
    r = servico.executar({"tickers": ["PETR4"]}, CsvFonte(pasta))
    x = r["operacoes"]["lista"][0]
    assert x["preco_entrada_bolsa"] == pytest.approx(4 * x["preco_entrada"])
    assert "na bolsa, a PETR4 abriu a R$" in r["roteiro_treino"]["exemplo"]
    sem = servico.executar({"tickers": ["PETR4"]}, CsvFonte(pasta_sintetica))
    assert sem["operacoes"]["lista"][0]["preco_entrada_bolsa"] is None and "Esses são preços ajustados" in sem["roteiro_treino"]["exemplo"]


# ------------------------------------------------------------------ procedência: só pregões fechados e registro da coleta
def test_so_dias_fechados_tira_o_pregao_do_dia():
    from datetime import date
    df = pd.DataFrame({"Close": [10.0, 11.0, 12.0]}, index=pd.to_datetime(["2026-11-05", "2026-11-06", "2026-11-09"]))
    fechados = dados.so_dias_fechados(df, hoje=date(2026, 11, 9))
    assert list(fechados.index.strftime("%Y-%m-%d")) == ["2026-11-05", "2026-11-06"]
    assert len(dados.so_dias_fechados(df, hoje=date(2026, 11, 10))) == 3      # baixado no dia seguinte, o 09/11 já fechou


def test_registrar_coleta_grava_data_fonte_ultimo_dado_e_hash(tmp_path):
    import hashlib
    from datetime import datetime
    serie_ohlc(30, 1, inicio="2026-09-01").to_csv(tmp_path / "preco_PETR4_SA.csv")
    serie_ohlc(30, 2, inicio="2026-09-01", preco0=130000).to_csv(tmp_path / "preco_idx_BVSP.csv")
    pd.DataFrame({"valor": [0.05, 0.05]}, index=pd.to_datetime(["2026-11-05", "2026-11-06"]).rename("data")).to_csv(tmp_path / "sgs_11.csv")

    agora = datetime(2026, 11, 14, 4, 2, tzinfo=dados.timezone.utc)      # 01:02 em Brasília
    coleta = dados.registrar_coleta(tmp_path, agora=agora)

    assert coleta["coletado_em"] == "2026-11-14T01:02-03:00"
    arqs = coleta["arquivos"]
    assert set(arqs) == {"preco_PETR4_SA.csv", "preco_idx_BVSP.csv", "sgs_11.csv"}
    assert arqs["preco_PETR4_SA.csv"]["fonte"] == "Yahoo Finance"
    assert arqs["preco_idx_BVSP.csv"]["fonte"].startswith("Ibovespa (B3)")
    assert arqs["sgs_11.csv"]["fonte"].startswith("Banco Central")
    assert arqs["sgs_11.csv"]["ultimo_dado"] == "2026-11-06" and arqs["sgs_11.csv"]["linhas"] == 2
    assert arqs["preco_PETR4_SA.csv"]["sha256"] == hashlib.sha256((tmp_path / "preco_PETR4_SA.csv").read_bytes()).hexdigest()
    assert dados.ler_coleta(tmp_path) == coleta


def test_ler_coleta_sem_arquivo_devolve_none(tmp_path):
    assert dados.ler_coleta(tmp_path) is None

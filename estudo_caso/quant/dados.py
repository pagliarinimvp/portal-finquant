"""Camada de dados plugável.

* `YFinanceFonte` – uso local: lê do cache CSV; se faltar/estiver defasado, baixa do
  Yahoo Finance (`auto_adjust=True`) e a Selic do SGS do Banco Central.
* `CsvFonte` – offline: só lê o cache. É a fonte pensada para o Portal FinQuant
  (sem rede em requisição); o cache é alimentado por `atualizar_cache()`.

Só preços diários. Devolve DataFrames com índice de datas SEM fuso horário.
"""
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from . import universo

COLUNAS_OHLCV = ["Open", "High", "Low", "Close", "Volume"]
COLUNA_FATOR = "FatorBolsa"    # preço que estava na bolsa ÷ preço ajustado, no mesmo dia (só para mostrar; as contas não usam)
SGS_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
SGS_SELIC_DIARIA = 11      # Selic over, % ao dia

# Fonte alternativa, usada só quando o SGS (api.bcb.gov.br) está fora do ar:
URL_COPOM = "https://www.bcb.gov.br/api/servico/sitebcb/historicotaxasjuros"     # meta Selic por reunião do Copom
SPREAD_SELIC_META = 0.10   # Selic over fica ~0,10 p.p. abaixo da meta Selic

# Filtro de qualidade dos preços (escolhas técnicas, calibradas na auditoria de 07/11/2026):
MAX_BURACO_DIAS = 10           # intervalo maior que isso entre pregões é falta de dados
MAX_FRACAO_SEM_VOLUME = 0.02   # acima disso, o preço ficou parado por falta de negócios na fonte
SALTO_SUSPEITO = 0.30          # variação em um dia que precisa ser confirmada pelo volume
MULTIPLO_VOLUME = 3.0          # salto real costuma vir com volume bem acima do normal
JANELA_VOLUME = 20             # pregões usados para medir o volume normal
MOVIMENTO_DE_MERCADO = 0.05    # com o Ibovespa variando isso no dia, o salto faz parte de um movimento geral


class DadosIndisponiveis(RuntimeError):
    """Não foi possível obter dados (sem cache e/ou sem rede)."""


def _limpar_indice(df: pd.DataFrame) -> pd.DataFrame:
    idx = pd.to_datetime(df.index)
    if idx.tz is not None:
        idx = idx.tz_localize(None)
    df = df.copy()
    df.index = idx.normalize()
    df.index.name = "Date"
    return df[~df.index.duplicated(keep="last")].sort_index()


class CsvFonte:
    """Lê apenas do cache em disco (um CSV por série)."""

    def __init__(self, pasta: str | Path = "cache_dados"):
        self.pasta = Path(pasta)
        self.avisos: list[str] = []      # notas sobre fontes alternativas usadas (a fachada repassa ao usuário)

    def _avisar(self, msg: str):
        if msg not in self.avisos:
            self.avisos.append(msg)

    # -- caminhos --------------------------------------------------------------
    def _arq_preco(self, simbolo: str) -> Path:
        seguro = simbolo.replace("^", "idx_").replace("=", "_").replace(".", "_")
        return self.pasta / f"preco_{seguro}.csv"

    def _arq_sgs(self, codigo: int) -> Path:
        return self.pasta / f"sgs_{codigo}.csv"

    # -- leitura ---------------------------------------------------------------
    def _ler(self, arq: Path) -> pd.DataFrame | None:
        if not arq.exists():
            return None
        df = pd.read_csv(arq, index_col=0, parse_dates=True)
        return _limpar_indice(df) if len(df) else None

    def precos(self, ticker: str, inicio: str, fim: str) -> pd.DataFrame:
        """OHLCV ajustado do ativo (ticker B3 ou símbolo de índice) no período."""
        simbolo = universo.simbolo_yahoo(ticker)
        df = self._ler(self._arq_preco(simbolo))
        if df is None:
            raise DadosIndisponiveis(f"Sem dados em cache para {ticker}.")
        return self._recorte(df[COLUNAS_OHLCV], inicio, fim)

    def fator_bolsa(self, ticker: str) -> pd.Series | None:
        """Quanto multiplicar o preço ajustado para ter o preço que estava na tela da corretora naquele dia.

        O preço ajustado desconta os dividendos e os desdobramentos que vieram depois, por isso os preços antigos ficam
        menores. A simulação usa o ajustado, que mede o retorno total; o fator serve só para mostrar o preço da época.
        Cache antigo, sem a coluna: None."""
        df = self._ler(self._arq_preco(universo.simbolo_yahoo(ticker)))
        if df is None or COLUNA_FATOR not in df.columns:
            return None
        f = df[COLUNA_FATOR].dropna()
        return f if len(f) else None

    def serie_sgs(self, codigo: int, inicio: str, fim: str) -> pd.Series:
        df = self._ler(self._arq_sgs(codigo))
        if df is None:
            return self._aproximar(codigo, inicio, fim)
        return self._recorte(df, inicio, fim)["valor"]

    # -- fonte alternativa (SGS indisponível) ------------------------------------
    def _arq_copom(self) -> Path:
        return self.pasta / "copom_meta_selic.csv"

    def _meta_df(self) -> pd.DataFrame:
        df = self._ler(self._arq_copom())
        if df is None:
            raise DadosIndisponiveis("Sem histórico da meta Selic em cache.")
        return df

    def _aproximar(self, codigo: int, inicio: str, fim: str) -> pd.Series:
        """Selic: aproximada pela meta Selic do Copom, aplicada em cada pregão
        (a Selic over acompanha a meta menos ~0,10 p.p.)."""
        if codigo == SGS_SELIC_DIARIA:
            dias = self.precos(universo.SIMBOLO_IBOV, inicio, fim).index
            df = selic_aproximada(self._meta_df(), dias)
            self._avisar(f"Selic APROXIMADA pela meta Selic do Copom (menos {SPREAD_SELIC_META:.2f} p.p.), pois a "
                         "API do SGS/Banco Central está inacessível.")
            return df["valor"]
        raise DadosIndisponiveis(f"Sem série SGS {codigo} em cache e sem fonte alternativa.")

    @staticmethod
    def _recorte(df: pd.DataFrame, inicio: str, fim: str) -> pd.DataFrame:
        fim_ts = pd.Timestamp(fim) if fim else pd.Timestamp(date.today())
        return df.loc[pd.Timestamp(inicio):fim_ts]


class YFinanceFonte(CsvFonte):
    """Cache + download. Baixa de novo se o arquivo for velho ou não cobrir o início."""

    def __init__(self, pasta: str | Path = "cache_dados", validade_horas: float = 12.0):
        super().__init__(pasta)
        self.pasta.mkdir(parents=True, exist_ok=True)
        self.validade_horas = validade_horas

    def _fresco(self, arq: Path) -> bool:
        return arq.exists() and (time.time() - arq.stat().st_mtime) < self.validade_horas * 3600

    # -- preços ----------------------------------------------------------------
    def precos(self, ticker: str, inicio: str, fim: str) -> pd.DataFrame:
        simbolo = universo.simbolo_yahoo(ticker)
        arq = self._arq_preco(simbolo)
        df = self._ler(arq)
        cobre = df is not None and df.index.min() <= pd.Timestamp(inicio) + timedelta(days=15)
        if not (cobre and self._fresco(arq)):
            try:
                novo = self._baixar_preco(simbolo, inicio)
                novo.to_csv(arq)
                df = novo
            except Exception as e:  # noqa: BLE001 – cai para o cache, se houver
                if df is None:
                    raise DadosIndisponiveis(f"Falha ao baixar {ticker}: {e}") from e
                self._avisar(f"Não foi possível atualizar {ticker}: usando os preços guardados, até {df.index.max().strftime('%d/%m/%Y')}.")
        return self._recorte(df[COLUNAS_OHLCV], inicio, fim)

    @staticmethod
    def _baixar_preco(simbolo: str, inicio: str) -> pd.DataFrame:
        import yfinance as yf  # import tardio: o núcleo roda offline sem yfinance carregado

        h = yf.Ticker(simbolo).history(start=inicio, interval="1d", auto_adjust=True)
        if h is None or h.empty:
            raise DadosIndisponiveis(f"Yahoo Finance sem dados para {simbolo}.")
        h = _limpar_indice(h)
        for c in COLUNAS_OHLCV:
            if c not in h.columns:
                h[c] = float("nan")
        h = h[COLUNAS_OHLCV].dropna(subset=["Close"])
        h = h[h["Close"] > 0]
        try:                                    # o fator é só para mostrar: se falhar, os preços ajustados seguem valendo
            h[COLUNA_FATOR] = _fator_bolsa(yf.Ticker(simbolo).history(start=inicio, interval="1d", auto_adjust=False, actions=True), h["Close"])
        except Exception:  # noqa: BLE001
            pass
        return h

    # -- SGS -------------------------------------------------------------------
    def serie_sgs(self, codigo: int, inicio: str, fim: str) -> pd.Series:
        arq = self._arq_sgs(codigo)
        df = self._ler(arq)
        cobre = df is not None and df.index.min() <= pd.Timestamp(inicio) + timedelta(days=45)
        if not (cobre and self._fresco(arq)):
            try:
                novo = self._baixar_sgs(codigo, inicio)
                novo.to_csv(arq)
                df = novo
            except Exception as e:  # noqa: BLE001
                if df is None:
                    try:
                        return self._aproximar(codigo, inicio, fim)
                    except Exception as e2:  # noqa: BLE001
                        raise DadosIndisponiveis(
                            f"sem acesso ao SGS/Banco Central (série {codigo}: {type(e).__name__}) "
                            f"e a fonte alternativa também falhou ({type(e2).__name__})") from e
                self._avisar(f"Não foi possível atualizar a Selic: usando os dados guardados, até {df.index.max().strftime('%d/%m/%Y')}.")
        return self._recorte(df, inicio, fim)["valor"]

    # -- fonte alternativa com download --------------------------------------------
    def _meta_df(self) -> pd.DataFrame:
        arq = self._arq_copom()
        df = self._ler(arq)
        if df is None or not self._fresco(arq):
            try:
                novo = self._baixar_meta_selic()
                novo.to_csv(arq)
                df = novo
            except Exception as e:  # noqa: BLE001
                if df is None:
                    raise DadosIndisponiveis(f"download falhou ({type(e).__name__})") from e
        return df

    @staticmethod
    def _baixar_meta_selic() -> pd.DataFrame:
        import requests

        r = requests.get(URL_COPOM, timeout=30)
        r.raise_for_status()
        linhas = []
        for x in r.json()["conteudo"]:
            if x.get("MetaSelic") is None or not x.get("DataInicioVigencia"):
                continue
            linhas.append((x["DataInicioVigencia"][:10], float(x["MetaSelic"])))   # meta % a.a.
        df = pd.DataFrame(linhas, columns=["data", "meta"])
        df["data"] = pd.to_datetime(df["data"])
        df = df[df["data"] >= "1999-03-05"]            # antes disso a meta não era anual
        if df.empty:
            raise DadosIndisponiveis("Histórico da meta Selic vazio.")
        return _limpar_indice(df.set_index("data")[["meta"]])

    @staticmethod
    def _baixar_sgs(codigo: int, inicio: str) -> pd.DataFrame:
        import requests

        # A API do SGS limita séries diárias a janelas de 10 anos: pedimos em blocos de 5.
        ini, hoje = pd.Timestamp(inicio), pd.Timestamp(date.today())
        partes, atual = [], ini
        while atual <= hoje:
            ate = min(atual + pd.DateOffset(years=5), hoje)
            r = requests.get(
                SGS_URL.format(codigo=codigo),
                params={"formato": "json",
                        "dataInicial": atual.strftime("%d/%m/%Y"),
                        "dataFinal": ate.strftime("%d/%m/%Y")},
                timeout=30,
            )
            r.raise_for_status()
            partes.append(pd.DataFrame(r.json()))
            atual = ate + timedelta(days=1)
        df = pd.concat([p for p in partes if len(p)], ignore_index=True)
        if df.empty:
            raise DadosIndisponiveis(f"SGS {codigo} sem dados.")
        df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
        df = df.dropna().drop_duplicates("data").set_index("data")[["valor"]]
        return _limpar_indice(df)


def selic_aproximada(meta: pd.DataFrame, dias: pd.DatetimeIndex, spread: float = SPREAD_SELIC_META) -> pd.DataFrame:
    """Taxa % ao dia por pregão a partir da meta Selic (% a.a., base 252) vigente em cada dia."""
    m = meta["meta"].sort_index()
    vigente = m.reindex(m.index.union(dias)).ffill().reindex(dias).bfill()
    taxa_aa = (vigente - spread).clip(lower=0.0)
    return pd.DataFrame({"valor": ((1.0 + taxa_aa / 100.0) ** (1.0 / 252.0) - 1.0) * 100.0}, index=dias)


def _fator_bolsa(bruto: pd.DataFrame, ajustado: pd.Series) -> pd.Series:
    """Preço da bolsa ÷ preço ajustado, dia a dia.

    O `Close` sem ajuste do Yahoo ainda vem corrigido pelos desdobramentos. Para voltar ao preço da época, ele é multiplicado
    pelas proporções dos desdobramentos que vieram depois de cada dia (um desdobramento de 1 para 2 tem proporção 2)."""
    bruto = _limpar_indice(bruto)
    desdobra = bruto.get("Stock Splits", pd.Series(0.0, index=bruto.index)).replace(0, 1.0).fillna(1.0)
    depois = desdobra[::-1].cumprod()[::-1].shift(-1).fillna(1.0)       # produto dos desdobramentos posteriores ao dia
    da_epoca = (bruto["Close"] * depois).reindex(ajustado.index)
    return (da_epoca / ajustado).round(6)


def criar_fonte(tipo: str, pasta: str | Path = "cache_dados") -> CsvFonte:
    return CsvFonte(pasta) if tipo == "csv" else YFinanceFonte(pasta)


def carregar_ativos(fonte: CsvFonte, tickers: list[str], inicio: str, fim: str, min_barras: int = 200):
    """Baixa vários ativos. Devolve ({ticker: OHLCV}, [avisos]); falhas viram aviso."""
    dados, avisos = {}, []
    for t in tickers:
        try:
            df = fonte.precos(t, inicio, fim)
        except DadosIndisponiveis as e:
            avisos.append(f"{t}: {e}")
            continue
        if len(df) < min_barras:
            avisos.append(f"{t}: histórico curto ({len(df)} pregões), ficou de fora da análise.")
            continue
        dados[t] = df
    return dados, avisos


def alinhar_fechamentos(dados: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Matriz de fechamentos pela interseção de datas (sem preenchimento de lacunas)."""
    fech = pd.DataFrame({t: d["Close"] for t, d in dados.items()})
    return fech.dropna(how="any")


def problemas_de_dados(df: pd.DataFrame, ret_ibov: pd.Series | None = None) -> list[str]:
    """Sinais de erro nos preços: buraco de datas, preço parado sem negócios e salto sem explicação.

    Um salto é aceito se veio com o mercado todo em forte movimento ou com volume bem acima do normal."""
    problemas = []
    buraco = df.index.to_series().diff().dt.days.max()
    if buraco == buraco and buraco > MAX_BURACO_DIAS:
        problemas.append(f"tem um intervalo de {int(buraco)} dias sem dados")
    fracao = float((df["Volume"] == 0).mean())
    if fracao > MAX_FRACAO_SEM_VOLUME:
        problemas.append(f"tem {100 * fracao:.0f}% dos dias sem negócios registrados".replace(".", ","))
    variacao = df["Close"].pct_change()
    normal = df["Volume"].shift(1).rolling(JANELA_VOLUME, min_periods=1).median()
    for dia in variacao.index[variacao.abs() > SALTO_SUSPEITO]:
        mercado = abs(ret_ibov.get(dia, 0.0)) if ret_ibov is not None else 0.0
        if mercado < MOVIMENTO_DE_MERCADO and df.loc[dia, "Volume"] <= MULTIPLO_VOLUME * normal.loc[dia]:
            problemas.append(f"variou {100 * variacao.loc[dia]:+.0f}% em {dia.strftime('%d/%m/%Y')}, sem movimento do mercado nem volume que explique")
    return problemas


def atualizar_cache(tickers: list[str], inicio: str, pasta: str | Path = "cache_dados") -> list[str]:
    """Baixa preços, Ibovespa e Selic para o cache (alimenta o `CsvFonte` do Portal)."""
    fonte = YFinanceFonte(pasta, validade_horas=0)
    fim = date.today().isoformat()
    falhas = []
    for t in [*tickers, universo.SIMBOLO_IBOV]:
        try:
            fonte.precos(t, inicio, fim)
        except DadosIndisponiveis as e:
            falhas.append(str(e))
    try:
        fonte.serie_sgs(SGS_SELIC_DIARIA, inicio, fim)
    except DadosIndisponiveis as e:
        falhas.append(str(e))
    return falhas

"""Roda a análise fora da requisição e guarda o resultado.

No Render gratuito, a seleção automática passa do limite de 30 s de uma requisição. Por isso a análise roda numa thread,
uma por vez (`_TRAVA`: o servidor tem 512 MB e pouco processador), e a página "Calculando…" consulta o andamento.
O resultado vai compactado para o cache `analises` (tabela no banco), que sobrevive à hibernação e aos deploys.

A chave junta a versão do núcleo, a configuração e a data do último pregão nos CSVs: com dados novos, a chave muda.

Pré-cálculo no tempo ocioso (`precalcular_ocioso`): com o custo e o capital fixos, as escolhas mais lentas são finitas.
Uma thread calcula, uma por vez, as 60 seleções automáticas e cada ação sozinha com os padrões, só de madrugada
(`janela()`, horário de Brasília), e cede a vez a quem pedir uma análise: na próxima troca de etapa, abandona o cálculo e
tenta de novo quando a fila esvaziar. Os preços novos chegam no deploy de sábado à 01:00 (.github/workflows), logo antes.
"""
import json
import logging
import threading
import time
import zlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

from django.conf import settings
from django.core.cache import caches
from django.db import connection

from .forms import PADROES
from .quant import config as c
from .quant import servico
from .quant.dados import SGS_SELIC_DIARIA, CsvFonte, DadosIndisponiveis, ler_coleta
from .quant.universo import IBOVESPA, SIMBOLO_IBOV, simbolo_yahoo

log = logging.getLogger(__name__)

_TRAVA = threading.Lock()          # uma análise por vez
_FILA_TRAVA = threading.Lock()     # protege a fila abaixo
_FILA: list[str] = []              # chaves em andamento, na ordem de chegada; a primeira é a que está rodando
VALIDADE_RESULTADO = 60 * 60 * 24 * 30      # a chave já muda com dados novos; isto só limpa o que ninguém usa
VALIDADE_ESTADO = 60 * 10


def _cache():
    return caches["analises"]


def pasta_dados() -> Path:
    return Path(settings.DADOS_ESTUDO)


def ultimo_pregao() -> str:
    """A data da última linha do Ibovespa nos CSVs (AAAA-MM-DD). Entra na chave do resultado."""
    arq = pasta_dados() / "preco_idx_BVSP.csv"
    try:
        with open(arq, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 400))
            ultima = f.read().decode().strip().splitlines()[-1]
        return ultima.split(",")[0][:10]
    except (OSError, IndexError):
        return "sem-dados"


# Sobe quando um texto guardado no resultado muda (vem do núcleo, como a leitura), para não servir o texto antigo do cache.
REVISAO_TEXTOS = 3  # 2: custo e capital fixos (09/11/2026) · 3: procedência dos dados (09/11/2026)


def chave(cfg: dict) -> str:
    return f"{servico.VERSAO}.{REVISAO_TEXTOS}-{servico.chave_cache(cfg)}-{ultimo_pregao()}"


def config_completa(cfg: dict) -> dict:
    """No servidor, os dados vêm sempre dos CSVs: nada de internet durante uma requisição."""
    return {**cfg, "fonte": "csv", "pasta_cache": str(pasta_dados())}


def resultado(k: str) -> dict | None:
    bruto = _cache().get(f"res:{k}")
    return json.loads(zlib.decompress(bruto)) if bruto else None


def procedencia(res: dict, pasta: Path | None = None) -> dict | None:
    """De onde e de quando vieram os CSVs desta análise: data da coleta e, por série, fonte, último dado e hash (`coleta.json`).

    Sem `coleta.json` (dados de antes de 09/11/2026), None: a página só não mostra o quadro."""
    pasta = pasta or pasta_dados()
    coleta = ler_coleta(pasta)
    if not coleta:
        return None
    arquivos, fonte = coleta.get("arquivos", {}), CsvFonte(pasta)
    tickers = [x["ticker"] for x in res["selecao"]["ranking"]] if res.get("selecao") else res.get("tickers", [])
    nomes = {t: fonte._arq_preco(simbolo_yahoo(t)).name for t in tickers}
    nomes["Ibovespa"] = fonte._arq_preco(SIMBOLO_IBOV).name
    nomes["Selic"] = f"sgs_{SGS_SELIC_DIARIA}.csv" if f"sgs_{SGS_SELIC_DIARIA}.csv" in arquivos else "copom_meta_selic.csv"
    series = [{"serie": s, "arquivo": n, **arquivos[n]} for s, n in nomes.items() if n in arquivos]
    return {"coletado_em": coleta.get("coletado_em"), "series": series}


def _guardar(k: str, res: dict):
    try:
        res["procedencia"] = procedencia(res)
    except Exception:       # noqa: BLE001 — o quadro de procedência nunca pode impedir o resultado de ser guardado
        log.exception("Falha ao ler a procedência dos dados")
        res["procedencia"] = None
    _cache().set(f"res:{k}", zlib.compress(json.dumps(res).encode(), 6), VALIDADE_RESULTADO)


def estado(k: str) -> dict:
    """{"situacao": "na_fila" | "rodando" | "erro" | "parado", "etapa", "na_frente", "erro"}."""
    with _FILA_TRAVA:
        na_frente = _FILA.index(k) if k in _FILA else None
    guardado = _cache().get(f"estado:{k}") or {}
    if guardado.get("erro"):
        return {"situacao": "erro", "erro": guardado["erro"]}
    if na_frente is None:
        return {"situacao": "parado"}           # o servidor reiniciou no meio: a página recarrega e pede de novo
    if na_frente > 0:
        return {"situacao": "na_fila", "na_frente": na_frente}
    etapa = guardado.get("etapa") or ""
    return {"situacao": "rodando", "etapa": etapa, "rotulo": servico.ETAPAS.get(etapa, "Começando")}


def iniciar(cfg: dict, k: str) -> None:
    """Põe a análise na fila, se ainda não estiver. Um erro guardado é apagado: pedir de novo é tentar de novo."""
    with _FILA_TRAVA:
        if k in _FILA:
            return
        _FILA.append(k)
    _cache().delete(f"estado:{k}")
    threading.Thread(target=_rodar, args=(cfg, k), daemon=True, name=f"analise-{k[:12]}").start()


def rodar_agora(cfg: dict, k: str | None = None) -> dict:
    """Roda na mesma thread e guarda o resultado (usado pelo `precalcular_estudo`)."""
    k = k or chave(cfg)
    with _TRAVA:
        res = servico.executar(config_completa(cfg))
    _guardar(k, res)
    return res


def _rodar(cfg: dict, k: str) -> None:
    try:
        with _TRAVA:
            def progresso(etapa: str):
                _cache().set(f"estado:{k}", {"etapa": etapa}, VALIDADE_ESTADO)
            res = servico.executar(config_completa(cfg), ao_progresso=progresso)
            _guardar(k, res)
            _cache().delete(f"estado:{k}")
    except (ValueError, DadosIndisponiveis) as e:
        _cache().set(f"estado:{k}", {"erro": f"Não foi possível rodar a análise. {e} Tente outras ações."}, VALIDADE_ESTADO)
    except Exception:       # noqa: BLE001 — a thread não pode morrer calada: registra e avisa a página
        log.exception("Falha na análise %s", k)
        _cache().set(f"estado:{k}", {"erro": "Não foi possível rodar a análise por um erro no servidor. Tente de novo em alguns minutos."},
                     VALIDADE_ESTADO)
    finally:
        with _FILA_TRAVA:
            if k in _FILA:
                _FILA.remove(k)
        connection.close()      # a thread abriu a própria conexão com o banco (o cache fica numa tabela)


def tempo_previsto(cfg: dict) -> str:
    """Estimativa para a página de espera, a partir das medições no Render em 09/11/2026 (1 ação 15 a 17 s, 4 ações
    27 a 33 s, 10 ações 36 a 37 s, seleção automática 75 s sem cache; sem contar a fila). Ajuste se os tempos mudarem."""
    if cfg["selecao"] == "automatica":
        return "1 a 2 minutos"
    if len(cfg["tickers"]) == 1:
        return "cerca de 15 segundos"
    return "menos de 1 minuto"


# ------------------------------------------------------------------------------- pré-cálculo no tempo ocioso
BRASILIA = timezone(timedelta(hours=-3))    # sem horário de verão desde 2019
PAUSA_ENTRE = 2                 # respiro entre uma análise e outra
ESPERA_FILA = 5                 # de quanto em quanto tempo olha se a fila esvaziou
ESPERA_JANELA = 5 * 60          # fora da janela, olha o relógio a cada 5 min
PAUSA_INICIAL = 120             # nada de trabalho enquanto o servidor sobe (o 1º teste travou começando na subida)


class _Cedeu(Exception):
    """O pré-cálculo parou para dar a vez a uma análise pedida por alguém."""


def _alguem_esperando() -> bool:
    with _FILA_TRAVA:
        return bool(_FILA)


def configs_ociosas() -> list[dict]:
    """O que vale deixar pronto, das visitas mais prováveis às menos: os padrões, cada ação sozinha e as 60 automáticas."""
    base = dict(PADROES)
    auto = {**base, "selecao": "automatica", "tickers": []}
    lista = [base, auto] + [{**auto, "divisao": d} for d in c.DIVISOES]
    lista += [{**base, "tickers": [t]} for t in sorted(IBOVESPA)]
    lista += [{**auto, "medias": m, "protecao": p, "divisao": d}
              for m in [*c.MEDIAS, c.MEDIAS_PELO_TREINO] for p in c.PROTECOES for d in c.DIVISOES]
    vistas, unicas = set(), []
    for cfg in lista:
        k = servico.chave_cache(cfg)
        if k not in vistas:
            vistas.add(k)
            unicas.append(cfg)
    return unicas


def rodar_ocioso(cfg: dict, k: str) -> bool:
    """Calcula e guarda, se o servidor estiver livre. Devolve False se cedeu a vez, se estava ocupado ou se não deu."""
    if _alguem_esperando() or not _TRAVA.acquire(blocking=False):
        return False
    try:
        def progresso(etapa: str):
            if _alguem_esperando():
                raise _Cedeu
        res = servico.executar(config_completa(cfg), ao_progresso=progresso)
        _guardar(k, res)
        return True
    except _Cedeu:
        log.info("Pré-cálculo cedeu a vez a uma análise pedida: %s", k)
        return False
    except (ValueError, DadosIndisponiveis) as e:
        log.info("Pré-cálculo pulou %s: %s", k, e)
        return False
    finally:
        _TRAVA.release()


def janela() -> tuple[int, int] | None:
    """As horas de início e de fim, em Brasília: `settings.ESTUDO_JANELA` ("2-5" = das 02:00 às 05:00). A volta completa
    leva ~90 min no Render. Vazio ou ilegível: None, o pré-cálculo fica desligado."""
    try:
        inicio, fim = (int(x) for x in str(getattr(settings, "ESTUDO_JANELA", "")).split("-"))
    except ValueError:
        return None
    return (inicio, fim)


def na_janela(agora: datetime | None = None) -> bool:
    j = janela()
    if j is None:
        return False
    agora = agora or datetime.now(BRASILIA)
    return j[0] <= agora.astimezone(BRASILIA).hour < j[1]


def precalcular_ocioso(uma_volta: bool = False) -> int:
    """Laço da thread de pré-cálculo (iniciada pelo `apps.py` no gunicorn): uma volta por noite, dentro da `janela()`,
    refazendo só o que falta no cache. Com `uma_volta`, roda já, ignora o horário e devolve quantas guardou."""
    if not uma_volta:
        time.sleep(PAUSA_INICIAL)
    while True:
        if not uma_volta:
            while not na_janela():
                time.sleep(ESPERA_JANELA)
        guardadas = 0
        for cfg in configs_ociosas():
            if not uma_volta and not na_janela():
                log.info("Pré-cálculo: fim da janela, o resto fica para a próxima noite.")
                break
            try:
                k = chave(cfg)
                if _cache().has_key(f"res:{k}"):
                    continue
                while not rodar_ocioso(cfg, k):
                    if not _alguem_esperando() and _TRAVA.acquire(blocking=False):
                        _TRAVA.release()
                        break           # estava livre e mesmo assim não deu (dados faltando): segue para a próxima
                    time.sleep(ESPERA_FILA)
                else:
                    guardadas += 1
                    time.sleep(PAUSA_ENTRE)
            except Exception:   # noqa: BLE001 — a thread não pode morrer: registra e segue
                log.exception("Falha no pré-cálculo de %s", cfg)
            finally:
                connection.close()      # thread longa: não deixa a conexão envelhecer entre uma análise e outra
        log.info("Pré-cálculo: %d análises novas guardadas nesta noite.", guardadas)
        if uma_volta:
            return guardadas
        while na_janela():          # uma volta por noite: espera a janela acabar antes de esperar a próxima
            time.sleep(ESPERA_JANELA)

"""Roda a análise fora da requisição e guarda o resultado.

No Render gratuito, a seleção automática passa do limite de 30 s de uma requisição. Por isso a análise roda numa thread,
uma por vez (`_TRAVA`: o servidor tem 512 MB e pouco processador), e a página "Calculando…" consulta o andamento.
O resultado vai compactado para o cache `analises` (tabela no banco), que sobrevive à hibernação e aos deploys.

A chave junta a versão do núcleo, a configuração e a data do último pregão nos CSVs: com dados novos, a chave muda.
"""
import json
import logging
import threading
import zlib
from pathlib import Path

from django.conf import settings
from django.core.cache import caches
from django.db import connection

from .quant import servico
from .quant.dados import DadosIndisponiveis

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


def chave(cfg: dict) -> str:
    return f"{servico.VERSAO}-{servico.chave_cache(cfg)}-{ultimo_pregao()}"


def config_completa(cfg: dict) -> dict:
    """No servidor, os dados vêm sempre dos CSVs: nada de internet durante uma requisição."""
    return {**cfg, "fonte": "csv", "pasta_cache": str(pasta_dados())}


def resultado(k: str) -> dict | None:
    bruto = _cache().get(f"res:{k}")
    return json.loads(zlib.decompress(bruto)) if bruto else None


def _guardar(k: str, res: dict):
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
    """Estimativa para a página de espera, a partir das medições no Render (ajuste se os tempos mudarem)."""
    if cfg["selecao"] == "automatica":
        return "cerca de 1 minuto"
    return "alguns segundos" if len(cfg["tickers"]) <= 4 else "menos de 1 minuto"

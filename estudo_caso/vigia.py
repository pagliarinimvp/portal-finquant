"""Vigia de travamento: se o servidor parar de responder, grava no log onde cada thread está parada.

Criado depois de o primeiro teste do pré-cálculo no Render (09/11/2026) deixar o site sem responder por ~10 min, sem
nenhum erro no log. Duas camadas, ligadas só no gunicorn (`apps.py`):

* `VigiaMiddleware` anota cada requisição em andamento; a thread `vigia` confere a cada `INTERVALO` segundos e, se
  alguma passar de `LIMITE` segundos, despeja a pilha de todas as threads (no máximo uma vez a cada `ENTRE_DESPEJOS`).
* Se nem a thread do vigia conseguir rodar (o processo inteiro congelado), o alarme do `faulthandler`, que roda fora do
  Python, dispara depois de `ALARME` segundos sem ser rearmado e despeja a pilha do mesmo jeito.
"""
import faulthandler
import logging
import sys
import threading
import time

log = logging.getLogger(__name__)

LIMITE = 30             # uma requisição presa há mais que isso é suspeita
INTERVALO = 10          # de quanto em quanto tempo o vigia confere (e rearma o alarme)
ALARME = 60             # sem rearmar por esse tempo, o faulthandler despeja a pilha sozinho
ENTRE_DESPEJOS = 600    # no máximo um despejo a cada 10 min, para não lotar o log

_TRAVA = threading.Lock()
_EM_CURSO: dict[int, tuple[float, str]] = {}    # thread -> (início, caminho)


class VigiaMiddleware:
    """Anota as requisições em andamento. Fica no topo do MIDDLEWARE; fora do gunicorn, só anota (não custa nada)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        i = threading.get_ident()
        with _TRAVA:
            _EM_CURSO[i] = (time.monotonic(), request.path)
        try:
            return self.get_response(request)
        finally:
            with _TRAVA:
                _EM_CURSO.pop(i, None)


def presas(agora: float | None = None) -> list[tuple[float, str]]:
    """As requisições em andamento há mais de `LIMITE` segundos: [(segundos, caminho)]."""
    agora = time.monotonic() if agora is None else agora
    with _TRAVA:
        return [(agora - t, p) for t, p in _EM_CURSO.values() if agora - t > LIMITE]


def _despejar(motivo: str) -> None:
    log.error("Vigia: %s. Pilha de todas as threads abaixo.", motivo)
    sys.stderr.flush()
    faulthandler.dump_traceback(file=sys.stderr, all_threads=True)
    sys.stderr.flush()


def _vigiar() -> None:
    ultimo = -ENTRE_DESPEJOS
    while True:
        faulthandler.dump_traceback_later(ALARME, exit=False, file=sys.stderr)    # rearma: só dispara se o vigia parar
        time.sleep(INTERVALO)
        lista = presas()
        agora = time.monotonic()
        if lista and agora - ultimo > ENTRE_DESPEJOS:
            ultimo = agora
            _despejar(f"{len(lista)} requisição(ões) presa(s): " + ", ".join(f"{p} há {s:.0f} s" for s, p in lista))


def iniciar() -> None:
    threading.Thread(target=_vigiar, daemon=True, name="vigia").start()

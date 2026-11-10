"""Limite de tentativas de login: 5 senhas erradas bloqueiam o usuário por 15 minutos.

O contador fica no cache `default` (LocMemCache, em memória). Isso basta
porque o Render roda um processo só (`--workers 1` no render.yaml); com mais
processos, cada um teria o próprio contador e o cache precisaria ser
compartilhado (banco ou Redis).

A chave é o nome de usuário, não o IP: atrás do Render e do Cloudflare o IP
real vem do X-Forwarded-For, que o próprio cliente pode forjar. O custo é que
alguém que erre a senha de propósito trava aquele usuário por 15 minutos; o
"Esqueci a senha" continua funcionando nesse intervalo.
"""
import hashlib

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.dispatch import receiver

MAX_FALHAS = 5
JANELA_SEGUNDOS = 15 * 60
MENSAGEM = (
    'Muitas tentativas de entrar com este usuário. Aguarde 15 minutos e tente '
    'de novo, ou use "Esqueci a senha".'
)


def _chave(usuario):
    normalizado = (usuario or '').strip().lower().encode()
    return 'login-falhas:' + hashlib.sha256(normalizado).hexdigest()


def bloqueado(usuario):
    return bool(usuario) and cache.get(_chave(usuario), 0) >= MAX_FALHAS


def registrar_falha(usuario):
    if not usuario:
        return
    chave = _chave(usuario)
    # O prazo conta da primeira falha: o incr não renova a validade da chave.
    cache.add(chave, 0, JANELA_SEGUNDOS)
    try:
        cache.incr(chave)
    except ValueError:  # a chave expirou entre o add e o incr
        cache.set(chave, 1, JANELA_SEGUNDOS)


def limpar(usuario):
    cache.delete(_chave(usuario))


class BackendComLimite(ModelBackend):
    """ModelBackend que recusa usuário bloqueado antes de conferir a senha.

    Fica em primeiro lugar no AUTHENTICATION_BACKENDS: o PermissionDenied
    interrompe todos os backends (inclusive o do allauth), então o bloqueio
    vale na tela de Entrar e no login do /admin/.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if bloqueado(username):
            raise PermissionDenied(MENSAGEM)
        return super().authenticate(request, username=username, password=password, **kwargs)


@receiver(user_login_failed)
def _ao_falhar(sender, credentials, request=None, **kwargs):
    registrar_falha(credentials.get('username'))


@receiver(user_logged_in)
def _ao_entrar(sender, request, user, **kwargs):
    limpar(user.get_username())

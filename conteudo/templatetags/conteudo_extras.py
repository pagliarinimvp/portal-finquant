import math
import re

import bleach
from django import template
from django.templatetags.static import static
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe

register = template.Library()

TAGS_PERMITIDAS = [
    'p', 'br', 'strong', 'em', 'b', 'i',
    'h2', 'h3', 'h4',
    'a', 'img', 'figure', 'figcaption',
    'ul', 'ol', 'li',
    'blockquote', 'code', 'pre',
    # Quadros ("Em 30 segundos", sumário, "Na prática", glossário).
    'aside', 'dl', 'dt', 'dd',
]

# Os quadros só aceitam uma destas classes; qualquer outra é removida.
CLASSES_DE_QUADRO = {'fq-em-30s', 'fq-sumario', 'fq-na-pratica', 'fq-glossario'}

# Âncora das seções, usada pelos links do sumário.
ID_DE_SECAO = re.compile(r'^[a-z0-9-]{1,80}$')

PALAVRAS_POR_MINUTO = 200


def _atributo_permitido(tag, nome, valor):
    if tag == 'a':
        return nome in ('href', 'rel', 'target')
    if tag == 'img':
        return nome in ('src', 'alt', 'width', 'height')
    if tag == 'aside':
        return nome == 'class' and valor in CLASSES_DE_QUADRO
    if tag == 'h2':
        return nome == 'id' and bool(ID_DE_SECAO.match(valor))
    return False


def _abrir_em_nova_aba(attrs, new=False):
    # Links internos da página (sumário) ficam na mesma aba, sem target/rel
    # vindos do texto.
    if attrs.get((None, 'href'), '').startswith('#'):
        attrs.pop((None, 'target'), None)
        attrs.pop((None, 'rel'), None)
        return attrs
    attrs[(None, 'rel')] = 'nofollow noopener'
    attrs[(None, 'target')] = '_blank'
    return attrs


@register.filter(name='corpo_seguro')
def corpo_seguro(valor):
    limpo = bleach.clean(valor, tags=TAGS_PERMITIDAS, attributes=_atributo_permitido)
    limpo = bleach.linkify(
        limpo,
        callbacks=[_abrir_em_nova_aba],
        skip_tags=['pre', 'code'],
        parse_email=False,
    )
    return mark_safe(limpo)


@register.filter(name='tempo_leitura')
def tempo_leitura(corpo):
    """Minutos de leitura do corpo, contando só as palavras (sem HTML)."""
    palavras = len(strip_tags(corpo or '').split())
    return max(1, math.ceil(palavras / PALAVRAS_POR_MINUTO))


@register.filter(name='capa_url')
def capa_url(caminho):
    """Endereço da capa, ou '' se não houver ou se o arquivo não estiver no deploy.

    Em produção, `static()` levanta ValueError para arquivo fora do manifesto
    do Whitenoise; a página abre sem a capa em vez de dar erro 500.
    """
    if not caminho:
        return ''
    try:
        return static(caminho)
    except ValueError:
        return ''

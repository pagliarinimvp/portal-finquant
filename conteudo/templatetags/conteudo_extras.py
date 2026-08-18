import bleach
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

TAGS_PERMITIDAS = [
    'p', 'br', 'strong', 'em', 'b', 'i',
    'h2', 'h3', 'h4',
    'a', 'img', 'figure', 'figcaption',
    'ul', 'ol', 'li',
    'blockquote', 'code', 'pre',
]

ATRIBUTOS_PERMITIDOS = {
    'a': ['href', 'rel', 'target'],
    'img': ['src', 'alt', 'width', 'height'],
}


def _abrir_em_nova_aba(attrs, new=False):
    attrs[(None, 'rel')] = 'nofollow noopener'
    attrs[(None, 'target')] = '_blank'
    return attrs


@register.filter(name='corpo_seguro')
def corpo_seguro(valor):
    limpo = bleach.clean(valor, tags=TAGS_PERMITIDAS, attributes=ATRIBUTOS_PERMITIDOS)
    limpo = bleach.linkify(
        limpo,
        callbacks=[_abrir_em_nova_aba],
        skip_tags=['pre', 'code'],
        parse_email=False,
    )
    return mark_safe(limpo)

import time

from django.conf import settings
from django.templatetags.static import static

from . import seo as _seo


def versao_estatico(request):
    """Sufixo `?v=...` dos CSS/JS próprios, só em desenvolvimento.

    Com DEBUG ligado, o sufixo muda a cada segundo e qualquer edição aparece
    sem hard refresh. Em produção ele fica vazio: o Whitenoise já põe o hash
    do conteúdo no nome do arquivo (site.70803a0a1c3a.css), e um sufixo que
    muda a cada requisição obrigava o navegador a baixar o arquivo de novo em
    toda página.
    """
    return {'versao_estatico': f'?v={int(time.time())}' if settings.DEBUG else ''}


def seo(request):
    """Título, descrição, endereço e imagem da página para buscadores e prévias.

    Os valores por rota ficam em `core/seo.py`. Uma view pode sobrepor
    `seo_titulo` e `seo_descricao` no próprio contexto, que tem prioridade
    sobre o de um context processor.
    """
    rota = request.resolver_match.view_name if request.resolver_match else ''
    titulo, descricao = _seo.titulo_e_descricao(rota)
    return {
        'seo_titulo': titulo,
        'seo_descricao': descricao,
        'seo_site': _seo.SITE,
        # Endereço sem a query string: as variações (?categoria=, ?tela=)
        # apontam para a mesma página nos buscadores.
        'seo_url': request.build_absolute_uri(request.path),
        'seo_imagem': request.build_absolute_uri(static('img/previa.png')),
    }

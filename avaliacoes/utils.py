from .models import Avaliacao

# Marca na sessão quem já enviou uma avaliação, para barrar a segunda resposta
# de quem não está logado (o usuário logado é barrado pelo banco).
CHAVE_SESSAO_AVALIOU = 'avaliacao_enviada'


def ja_avaliou(request):
    """Diz se quem fez a requisição já respondeu a avaliação.

    Evita respostas duplicadas, que distorcem as médias da análise do TCC.
    Para anônimos vale só no mesmo navegador (a sessão dura duas semanas);
    na exportação, as duplicadas restantes ainda precisam ser filtradas.
    """
    if request.session.get(CHAVE_SESSAO_AVALIOU):
        return True
    if request.user.is_authenticated:
        return Avaliacao.objects.filter(usuario=request.user).exists()
    return False


# Ids dos artigos que o visitante já avaliou nesta sessão ("Este artigo te ajudou?").
CHAVE_SESSAO_ARTIGOS = 'artigos_avaliados'


def avaliou_artigo(request, artigo):
    """Diz se quem fez a requisição já respondeu sobre este artigo (um voto por artigo)."""
    if artigo.pk in request.session.get(CHAVE_SESSAO_ARTIGOS, []):
        return True
    if request.user.is_authenticated:
        from .models import AvaliacaoArtigo
        return AvaliacaoArtigo.objects.filter(artigo=artigo, usuario=request.user).exists()
    return False


def marcar_artigo_avaliado(request, artigo):
    request.session[CHAVE_SESSAO_ARTIGOS] = request.session.get(CHAVE_SESSAO_ARTIGOS, []) + [artigo.pk]

from .models import Avaliacao


def modal_avaliacao(request):
    """Indica se o modal de aviso para avaliar o site deve ser injetado na página.

    Fica em False para quem já tem uma Avaliacao salva (usuário autenticado)
    e nas próprias páginas do app avaliacoes, onde pedir de novo não faz sentido.
    A supressão por sessão de navegador (dispensar/enviar) é feita no JS via
    sessionStorage, não aqui.
    """
    # resolver_match em vez de resolve(): fica None numa URL inexistente,
    # enquanto resolve() lançaria Resolver404 ao renderizar uma página 404.
    rota = getattr(request, 'resolver_match', None)
    if rota is not None and rota.app_name == 'avaliacoes':
        return {'mostrar_modal_avaliacao': False}

    if request.user.is_authenticated:
        ja_avaliou = Avaliacao.objects.filter(usuario=request.user).exists()
        return {'mostrar_modal_avaliacao': not ja_avaliou}

    return {'mostrar_modal_avaliacao': True}

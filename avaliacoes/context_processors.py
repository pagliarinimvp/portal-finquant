from .utils import ja_avaliou


def modal_avaliacao(request):
    """Indica se o modal de aviso para avaliar o site deve ser injetado na página.

    Fica em False para quem já avaliou (usuário logado com Avaliacao salva, ou
    sessão marcada depois do envio) e nas próprias páginas do app avaliacoes,
    onde pedir de novo não faz sentido. A supressão de quem só dispensou o
    aviso é feita no JS via sessionStorage, não aqui.
    """
    # resolver_match em vez de resolve(): fica None numa URL inexistente,
    # enquanto resolve() lançaria Resolver404 ao renderizar uma página 404.
    rota = getattr(request, 'resolver_match', None)
    if rota is not None and rota.app_name == 'avaliacoes':
        return {'mostrar_modal_avaliacao': False}

    return {'mostrar_modal_avaliacao': not ja_avaliou(request)}

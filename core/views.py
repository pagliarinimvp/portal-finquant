from django.http import HttpResponse
from django.shortcuts import redirect
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.cache import cache_control
from django.views.generic import TemplateView

from conteudo.models import Artigo


class HomeView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['artigos_recentes'] = Artigo.objects.filter(
            status=Artigo.Status.PUBLICADO
        ).order_by('-publicado_em')[:3]
        return context


def saude(request):
    # Rota para o monitor externo que mantém o Render acordado. Não pode tocar no
    # banco: um ping a cada 10 minutos deixaria o Neon ligado o mês inteiro,
    # acima das horas de computação do plano gratuito.
    return HttpResponse('ok', content_type='text/plain')


@cache_control(max_age=86400, public=True)
def robots_txt(request):
    # /estudo-caso/aviso/ e /estudo-caso/analise/ ficam fora: cada combinação de escolhas no link
    # dispara um cálculo pesado, e um robô seguindo as combinações ocuparia o
    # servidor gratuito. A página de escolhas (/estudo-caso/) continua aberta.
    linhas = [
        'User-agent: *',
        'Disallow: /admin/',
        'Disallow: /contas/',
        'Disallow: /avaliacao/',
        'Disallow: /estudo-caso/aviso/',
        'Disallow: /estudo-caso/analise/',
        'Disallow: /estudo-caso/status/',
        'Disallow: /estudo-caso/pdf/',
        '',
        f'Sitemap: {request.build_absolute_uri(reverse("sitemap"))}',
    ]
    return HttpResponse('\n'.join(linhas) + '\n', content_type='text/plain')


def favicon(request):
    # Navegadores e leitores de feed pedem /favicon.ico direto, sem ler o <link>
    # do <head>. O static() fica dentro da view porque, em produção, o nome do
    # arquivo leva o hash do manifesto do collectstatic.
    return redirect(static('img/favicon.ico'), permanent=False)

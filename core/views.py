from django.http import HttpResponse
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

from django.views.generic import TemplateView

from conteudo.models import Artigo


class HomeView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['artigos_recentes'] = Artigo.objects.order_by('-publicado_em')[:3]
        return context

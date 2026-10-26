from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView

from .forms import AvaliacaoForm
from .utils import CHAVE_SESSAO_AVALIOU, ja_avaliou


class AvaliacaoCreateView(CreateView):
    form_class = AvaliacaoForm
    template_name = 'avaliacoes/avaliacao_form.html'
    success_url = reverse_lazy('avaliacoes:obrigado')

    def dispatch(self, request, *args, **kwargs):
        # Uma resposta por pessoa: quem já avaliou vai direto para o obrigado.
        if ja_avaliou(request):
            messages.info(request, 'Você já avaliou o site. Obrigado pela participação!')
            return redirect('avaliacoes:obrigado')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['contato_email'] = settings.CONTATO_EMAIL
        return contexto

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.usuario = self.request.user
        resposta = super().form_valid(form)
        self.request.session[CHAVE_SESSAO_AVALIOU] = True
        return resposta

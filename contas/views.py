from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from .forms import CadastroForm


class CadastroView(CreateView):
    form_class = CadastroForm
    template_name = 'contas/cadastro.html'
    success_url = reverse_lazy('core:home')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Loga o usuário automaticamente após o cadastro, evitando um passo extra.
        # O backend é obrigatório aqui: com o allauth há dois em
        # AUTHENTICATION_BACKENDS, e sem ele o login() lança ValueError (500).
        login(self.request, self.object, backend='django.contrib.auth.backends.ModelBackend')
        return response


class MinhaContaView(LoginRequiredMixin, TemplateView):
    template_name = 'contas/minha_conta.html'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['avaliacoes'] = self.request.user.avaliacoes.all()
        return contexto

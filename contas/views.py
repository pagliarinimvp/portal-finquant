from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView


class CadastroView(CreateView):
    form_class = UserCreationForm
    template_name = 'contas/cadastro.html'
    success_url = reverse_lazy('core:home')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Loga o usuário automaticamente após o cadastro, evitando um passo extra.
        login(self.request, self.object)
        return response


class MinhaContaView(LoginRequiredMixin, TemplateView):
    template_name = 'contas/minha_conta.html'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['avaliacoes'] = self.request.user.avaliacoes.all()
        return contexto

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
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


class EsqueciSenhaView(auth_views.PasswordResetView):
    """Pedido de senha nova, ou um aviso quando o portal não consegue enviar e-mail.

    O Render gratuito bloqueia as portas SMTP: com o envio desligado
    (RECUPERACAO_SENHA_ATIVA=False), a tela pede para falar com o
    administrador em vez de prometer um e-mail que nunca chega.
    """

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['envio_ativo'] = settings.RECUPERACAO_SENHA_ATIVA
        contexto['contato_email'] = settings.CONTATO_EMAIL
        return contexto

    def post(self, request, *args, **kwargs):
        if not settings.RECUPERACAO_SENHA_ATIVA:
            return self.get(request, *args, **kwargs)
        return super().post(request, *args, **kwargs)

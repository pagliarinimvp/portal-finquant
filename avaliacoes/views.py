from django.urls import reverse_lazy
from django.views.generic.edit import CreateView

from .forms import AvaliacaoForm


class AvaliacaoCreateView(CreateView):
    form_class = AvaliacaoForm
    template_name = 'avaliacoes/avaliacao_form.html'
    success_url = reverse_lazy('avaliacoes:obrigado')

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.usuario = self.request.user
        return super().form_valid(form)

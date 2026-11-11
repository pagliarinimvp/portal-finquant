from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic.edit import CreateView

from conteudo.models import Artigo

from .forms import AvaliacaoArtigoForm, AvaliacaoForm
from .models import AvaliacaoArtigo
from .utils import CHAVE_SESSAO_AVALIOU, avaliou_artigo, ja_avaliou, marcar_artigo_avaliado


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


class AvaliarArtigoView(View):
    """Recebe o "Este artigo te ajudou?" e volta ao fim do artigo.

    Só artigos publicados recebem resposta (rascunho dá 404), e cada visitante
    responde uma vez por artigo; a segunda resposta é ignorada em silêncio.
    """

    http_method_names = ['post']

    def post(self, request, slug):
        artigo = get_object_or_404(Artigo, slug=slug, status=Artigo.Status.PUBLICADO)
        destino = artigo.get_absolute_url() + '#avaliacao-artigo'
        if avaliou_artigo(request, artigo):
            return redirect(destino)
        form = AvaliacaoArtigoForm(request.POST)
        if not form.is_valid():
            messages.error(request, 'Escolha "Sim" ou "Não" para responder.')
            return redirect(destino)
        AvaliacaoArtigo.objects.create(
            artigo=artigo,
            ajudou=form.cleaned_data['ajudou'],
            comentario=form.cleaned_data['comentario'],
            versao_revisada_em=artigo.revisado_em,
            usuario=request.user if request.user.is_authenticated else None,
        )
        marcar_artigo_avaliado(request, artigo)
        return redirect(destino)

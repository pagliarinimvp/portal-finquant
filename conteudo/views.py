from django.views.generic import DetailView, ListView

from avaliacoes.utils import avaliou_artigo

from .models import Artigo
from .templatetags.conteudo_extras import capa_url


class ArtigoListView(ListView):
    model = Artigo
    template_name = 'conteudo/artigo_list.html'
    context_object_name = 'artigos'
    paginate_by = 9

    def get_queryset(self):
        artigos = Artigo.objects.filter(status=Artigo.Status.PUBLICADO)
        # Categoria desconhecida na URL é ignorada: mostra a lista inteira.
        self.categoria_atual = self.request.GET.get('categoria', '')
        if self.categoria_atual in Artigo.Categoria.values:
            artigos = artigos.filter(categoria=self.categoria_atual)
        else:
            self.categoria_atual = ''
        return artigos

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['categorias'] = Artigo.Categoria.choices
        contexto['categoria_atual'] = self.categoria_atual
        return contexto


class ArtigoDetailView(DetailView):
    model = Artigo
    template_name = 'conteudo/artigo_detail.html'
    context_object_name = 'artigo'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        if self.request.user.is_staff:
            return Artigo.objects.all()
        return Artigo.objects.filter(status=Artigo.Status.PUBLICADO)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        # Prévia do link (Google, WhatsApp): o próprio artigo, não o padrão do site.
        contexto['seo_titulo'] = self.object.titulo
        contexto['seo_descricao'] = self.object.resumo
        contexto['ja_avaliou_artigo'] = avaliou_artigo(self.request, self.object)
        contexto['url_absoluta'] = self.request.build_absolute_uri(self.object.get_absolute_url())
        contexto['leia_tambem'] = self._leia_tambem(self.object)
        url_capa = capa_url(self.object.capa)
        if url_capa:
            contexto['seo_imagem'] = self.request.build_absolute_uri(url_capa)
            contexto['seo_imagem_alt'] = self.object.capa_alt
        return contexto

    @staticmethod
    def _leia_tambem(artigo, quantidade=3):
        """Até 3 artigos publicados: primeiro os da mesma categoria, depois os mais recentes."""
        publicados = Artigo.objects.filter(status=Artigo.Status.PUBLICADO).exclude(pk=artigo.pk)
        escolhidos = list(publicados.filter(categoria=artigo.categoria)[:quantidade])
        if len(escolhidos) < quantidade:
            outros = publicados.exclude(pk__in=[a.pk for a in escolhidos]).exclude(categoria=artigo.categoria)
            escolhidos += list(outros[:quantidade - len(escolhidos)])
        return escolhidos

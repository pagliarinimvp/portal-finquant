from django.views.generic import DetailView, ListView

from .models import Artigo


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

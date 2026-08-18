from django.views.generic import DetailView, ListView

from .models import Artigo


class ArtigoListView(ListView):
    model = Artigo
    template_name = 'conteudo/artigo_list.html'
    context_object_name = 'artigos'
    paginate_by = 9

    def get_queryset(self):
        return Artigo.objects.filter(status=Artigo.Status.PUBLICADO)


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

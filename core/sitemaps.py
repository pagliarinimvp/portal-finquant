from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from conteudo.models import Artigo


class PaginasFixasSitemap(Sitemap):
    changefreq = 'monthly'

    def items(self):
        return [
            'core:home', 'conteudo:lista', 'simuladores:index',
            'simuladores:juros_compostos', 'simuladores:divida_cartao',
            'simuladores:meta_financeira', 'estudo_caso:index',
        ]

    def location(self, item):
        return reverse(item)


class ArtigosSitemap(Sitemap):
    changefreq = 'monthly'

    def items(self):
        return Artigo.objects.filter(status=Artigo.Status.PUBLICADO)

    def lastmod(self, artigo):
        return artigo.atualizado_em


SITEMAPS = {'paginas': PaginasFixasSitemap, 'artigos': ArtigosSitemap}

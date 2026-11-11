from django.contrib import admin

from .models import Avaliacao, AvaliacaoArtigo


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = (
        'nota', 'usuario', 'faixa_etaria', 'sexo', 'experiencia_investimentos',
        'conteudo_ajudou', 'faixa_renda_familiar', 'consentimento', 'criado_em',
    )
    list_filter = (
        'nota', 'faixa_etaria', 'sexo', 'experiencia_investimentos',
        'conteudo_ajudou', 'faixa_renda_familiar',
    )
    readonly_fields = ('criado_em',)


@admin.register(AvaliacaoArtigo)
class AvaliacaoArtigoAdmin(admin.ModelAdmin):
    list_display = ('artigo', 'ajudou', 'versao_revisada_em', 'tem_comentario', 'usuario', 'criado_em')
    list_filter = ('ajudou', 'artigo', 'versao_revisada_em')
    search_fields = ('comentario', 'artigo__titulo')
    readonly_fields = ('criado_em',)

    @admin.display(boolean=True, description='Comentou')
    def tem_comentario(self, obj):
        return bool(obj.comentario)

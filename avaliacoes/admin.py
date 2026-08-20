from django.contrib import admin

from .models import Avaliacao


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = (
        'nota', 'usuario', 'faixa_etaria', 'sexo', 'experiencia_investimentos',
        'conteudo_ajudou', 'faixa_renda_familiar', 'criado_em',
    )
    list_filter = (
        'nota', 'faixa_etaria', 'sexo', 'experiencia_investimentos',
        'conteudo_ajudou', 'faixa_renda_familiar',
    )
    readonly_fields = ('criado_em',)

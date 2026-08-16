from django.contrib import admin

from .models import Artigo


@admin.register(Artigo)
class ArtigoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'publicado_em')
    list_filter = ('categoria',)
    search_fields = ('titulo', 'resumo', 'corpo')
    prepopulated_fields = {'slug': ('titulo',)}

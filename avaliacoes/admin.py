from django.contrib import admin

from .models import Avaliacao


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ('nota', 'usuario', 'criado_em')
    list_filter = ('nota',)
    readonly_fields = ('criado_em',)

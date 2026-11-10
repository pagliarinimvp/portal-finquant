from django.contrib import admin
from django.utils import timezone

from .models import Artigo


@admin.register(Artigo)
class ArtigoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'status', 'com_apoio_ia', 'publicado_em')
    list_filter = ('status', 'categoria', 'com_apoio_ia')
    fieldsets = (
        (None, {'fields': ('titulo', 'slug', 'resumo', 'corpo', 'categoria')}),
        ('Publicação', {'fields': ('status', 'publicado_em', 'com_apoio_ia')}),
        ('Capa', {'fields': ('capa', 'capa_alt', 'capa_credito')}),
    )
    search_fields = ('titulo', 'resumo', 'corpo')
    prepopulated_fields = {'slug': ('titulo',)}
    actions = ['marcar_como_publicado']

    @admin.action(description='Marcar selecionados como publicado')
    def marcar_como_publicado(self, request, queryset):
        # update() não passa pelo save() do modelo: a data vai aqui.
        queryset.filter(publicado_em__isnull=True).update(publicado_em=timezone.now())
        atualizados = queryset.update(status=Artigo.Status.PUBLICADO)
        self.message_user(request, f'{atualizados} artigo(s) publicado(s).')

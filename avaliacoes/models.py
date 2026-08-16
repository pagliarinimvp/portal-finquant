from django.conf import settings
from django.db import models


class Avaliacao(models.Model):
    class Nota(models.IntegerChoices):
        UM = 1, '1 - Muito ruim'
        DOIS = 2, '2 - Ruim'
        TRES = 3, '3 - Regular'
        QUATRO = 4, '4 - Bom'
        CINCO = 5, '5 - Excelente'

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='avaliacoes',
    )
    nota = models.IntegerField(choices=Nota.choices)
    comentario = models.TextField(blank=True, help_text='Opcional: conte o que podemos melhorar.')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Avaliação'
        verbose_name_plural = 'Avaliações'

    def __str__(self):
        quem = self.usuario.username if self.usuario else 'anônimo'
        return f'Nota {self.nota} de {quem}'

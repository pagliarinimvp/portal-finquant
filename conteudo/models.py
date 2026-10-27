from django.db import models
from django.db.models import F
from django.urls import reverse
from django.utils import timezone


class Artigo(models.Model):
    class Categoria(models.TextChoices):
        FUNDAMENTOS = 'FUNDAMENTOS', 'Fundamentos'
        RENDA_FIXA = 'RENDA_FIXA', 'Renda fixa'
        RENDA_VARIAVEL = 'RENDA_VARIAVEL', 'Renda variável'
        ANALISE_QUANTITATIVA = 'ANALISE_QUANTITATIVA', 'Análise quantitativa'

    class Status(models.TextChoices):
        RASCUNHO = 'RASCUNHO', 'Rascunho'
        PUBLICADO = 'PUBLICADO', 'Publicado'

    titulo = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, help_text='Usado na URL do artigo, gerado a partir do título.')
    resumo = models.CharField(max_length=300, help_text='Texto curto exibido na listagem.')
    corpo = models.TextField(help_text='Conteúdo completo do artigo (aceita um subconjunto seguro de HTML).')
    categoria = models.CharField(max_length=30, choices=Categoria.choices, default=Categoria.FUNDAMENTOS)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RASCUNHO)
    publicado_em = models.DateTimeField(
        null=True, blank=True,
        help_text='Preenchida sozinha na primeira vez que o artigo é publicado.',
    )
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [F('publicado_em').desc(nulls_last=True)]

    def save(self, *args, **kwargs):
        # A data é a da primeira publicação: voltar para rascunho e
        # republicar não muda a data.
        if self.status == self.Status.PUBLICADO and self.publicado_em is None:
            self.publicado_em = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse('conteudo:detalhe', args=[self.slug])

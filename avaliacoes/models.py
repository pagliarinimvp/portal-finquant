from django.conf import settings
from django.db import models


class Avaliacao(models.Model):
    class Nota(models.IntegerChoices):
        UM = 1, 'Muito ruim'
        DOIS = 2, 'Ruim'
        TRES = 3, 'Regular'
        QUATRO = 4, 'Bom'
        CINCO = 5, 'Excelente'

    class FaixaEtaria(models.TextChoices):
        # Desde 10/11/2026 a pesquisa é só para maiores de 18 anos. ATE_18 fica
        # apenas para ler respostas antigas; o formulário não oferece mais.
        ATE_18 = 'ATE_18', 'Até 18 anos (formulário antigo)'
        DE_18_A_25 = '18_25', '18 a 25 anos'
        DE_26_A_35 = '26_35', '26 a 35 anos'
        DE_36_A_45 = '36_45', '36 a 45 anos'
        DE_46_A_60 = '46_60', '46 a 60 anos'
        MAIS_60 = 'MAIS_60', 'Mais de 60 anos'

    class Sexo(models.TextChoices):
        MASCULINO = 'M', 'Masculino'
        FEMININO = 'F', 'Feminino'
        OUTRO = 'O', 'Outro'
        NAO_INFORMAR = 'NI', 'Prefiro não informar'

    class ExperienciaInvestimentos(models.IntegerChoices):
        NENHUMA = 1, 'Nenhuma (nunca investi)'
        INICIANTE = 2, 'Iniciante (poupança, Tesouro Direto, CDB)'
        INTERMEDIARIA = 3, 'Intermediária (ações, fundos imobiliários, ETFs)'
        AVANCADA = 4, 'Avançada (derivativos, day trade, fundos multimercado)'

    class ConteudoAjudou(models.IntegerChoices):
        DISCORDO_TOTALMENTE = 1, 'Discordo totalmente'
        DISCORDO = 2, 'Discordo'
        NEUTRO = 3, 'Neutro'
        CONCORDO = 4, 'Concordo'
        CONCORDO_TOTALMENTE = 5, 'Concordo totalmente'

    class FaixaRendaFamiliar(models.TextChoices):
        ATE_2000 = 'ATE_2000', 'Até R$ 2.000'
        DE_2000_A_5000 = '2000_5000', 'De R$ 2.000,01 a R$ 5.000'
        DE_5000_A_10000 = '5000_10000', 'De R$ 5.000,01 a R$ 10.000'
        MAIS_10000 = 'MAIS_10000', 'Acima de R$ 10.000'
        NAO_INFORMAR = 'NAO_INFORMAR', 'Prefiro não informar'

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='avaliacoes',
    )
    nota = models.IntegerField(choices=Nota.choices, verbose_name='Navegação no site')
    faixa_etaria = models.CharField(max_length=10, choices=FaixaEtaria.choices)
    sexo = models.CharField(max_length=2, choices=Sexo.choices)
    experiencia_investimentos = models.IntegerField(choices=ExperienciaInvestimentos.choices)
    conteudo_ajudou = models.IntegerField(choices=ConteudoAjudou.choices)
    faixa_renda_familiar = models.CharField(max_length=13, choices=FaixaRendaFamiliar.choices)
    comentario = models.TextField('Comentário', blank=True, help_text='Opcional: conte o que podemos melhorar.')
    # Registro do consentimento (LGPD, art. 7º, I): o formulário só é aceito
    # com a caixa marcada, e o valor fica salvo como prova junto da resposta.
    consentimento = models.BooleanField('Consentiu em participar da pesquisa', default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Avaliação'
        verbose_name_plural = 'Avaliações'

    def __str__(self):
        quem = self.usuario.username if self.usuario else 'anônimo'
        return f'Nota {self.nota} de {quem}'


class AvaliacaoArtigo(models.Model):
    """Resposta rápida ao "Este artigo te ajudou?", no fim de cada artigo.

    Complementa a pesquisa do site (`Avaliacao`) com um dado por artigo, para a
    análise de qualidade do TCC comparar conteúdos. É anônima (não pede dado
    pessoal); `usuario` só é guardado para quem está logado.
    """

    artigo = models.ForeignKey(
        'conteudo.Artigo', on_delete=models.PROTECT, related_name='avaliacoes',
        help_text='Artigo com respostas não pode ser apagado, para os dados do TCC não sumirem.',
    )
    ajudou = models.BooleanField('o artigo ajudou')
    comentario = models.TextField('Comentário', blank=True, max_length=1000)
    # Separa as respostas de cada versão do artigo quando o texto é substituído
    # (`exportar_artigo_migracao --substituir`), que mantém o mesmo artigo.
    versao_revisada_em = models.DateField(
        'versão (conteúdo revisado em)', null=True, blank=True,
        help_text='Valor de "conteúdo revisado em" do artigo no momento da resposta.',
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='avaliacoes_artigos',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Avaliação de artigo'
        verbose_name_plural = 'Avaliações de artigos'

    def __str__(self):
        return f'{"Ajudou" if self.ajudou else "Não ajudou"}: {self.artigo}'

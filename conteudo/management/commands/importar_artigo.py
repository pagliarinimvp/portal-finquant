import json

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from conteudo.models import Artigo


class Command(BaseCommand):
    help = (
        'Cria um Artigo como rascunho a partir de um arquivo JSON com os '
        'campos titulo, resumo, corpo (HTML) e categoria. Usado pela skill '
        'formatar-artigo para publicação automática (o artigo fica em modo '
        'rascunho até ser revisado e publicado no Admin).'
    )

    def add_arguments(self, parser):
        parser.add_argument('arquivo_json', help='Caminho para o arquivo JSON do artigo.')

    def handle(self, *args, **options):
        caminho = options['arquivo_json']
        try:
            with open(caminho, encoding='utf-8') as arquivo:
                dados = json.load(arquivo)
        except FileNotFoundError:
            raise CommandError(f'Arquivo não encontrado: {caminho}')
        except json.JSONDecodeError as erro:
            raise CommandError(f'JSON inválido em {caminho}: {erro}')

        for campo in ('titulo', 'resumo', 'corpo', 'categoria'):
            if not dados.get(campo):
                raise CommandError(f'Campo obrigatório ausente ou vazio: {campo}')

        titulo = dados['titulo']
        resumo = dados['resumo']
        corpo = dados['corpo']
        categoria = dados['categoria']

        if len(titulo) > 200:
            raise CommandError(f'"titulo" tem {len(titulo)} caracteres, o máximo é 200.')
        if len(resumo) > 300:
            raise CommandError(f'"resumo" tem {len(resumo)} caracteres, o máximo é 300.')
        if categoria not in Artigo.Categoria.values:
            opcoes = ', '.join(Artigo.Categoria.values)
            raise CommandError(f'"categoria" inválida: {categoria!r}. Opções: {opcoes}')

        slug_base = slugify(titulo)
        slug = slug_base
        sufixo = 2
        while Artigo.objects.filter(slug=slug).exists():
            slug = f'{slug_base}-{sufixo}'
            sufixo += 1

        artigo = Artigo.objects.create(
            titulo=titulo,
            slug=slug,
            resumo=resumo,
            corpo=corpo,
            categoria=categoria,
            status=Artigo.Status.RASCUNHO,
        )

        self.stdout.write(self.style.SUCCESS(
            f'Rascunho criado: "{artigo.titulo}" (slug={artigo.slug}).\n'
            f'Revise e publique em /admin/conteudo/artigo/{artigo.pk}/change/'
        ))

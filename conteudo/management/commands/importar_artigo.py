import json
from pathlib import PurePosixPath

from django.contrib.staticfiles import finders
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from conteudo.models import Artigo
from PIL import Image, UnidentifiedImageError

TAMANHO_CAPA = (1200, 630)
FORMATOS_CAPA = {'JPEG', 'PNG', 'WEBP'}


def validar_capa(capa, capa_alt, capa_credito):
    """Confere a capa antes de criar o artigo; levanta CommandError com o problema."""
    caminho = PurePosixPath(capa.replace('\\', '/'))
    if caminho.is_absolute() or '..' in caminho.parts or ':' in capa:
        raise CommandError(f'"capa" precisa ser um caminho dentro de static/, ex.: img/artigos/<slug>/capa.jpg (veio {capa!r}).')
    arquivo = finders.find(str(caminho))
    if not arquivo:
        raise CommandError(f'"capa" não encontrada em static/: {capa}')
    try:
        with Image.open(arquivo) as imagem:
            formato, tamanho = imagem.format, imagem.size
    except (UnidentifiedImageError, OSError):
        raise CommandError(f'"capa" não é uma imagem válida: {capa}')
    if formato not in FORMATOS_CAPA:
        raise CommandError(f'"capa" está em {formato}; use JPEG, PNG ou WEBP.')
    if tamanho != TAMANHO_CAPA:
        raise CommandError(
            f'"capa" tem {tamanho[0]}x{tamanho[1]} px; o tamanho exigido é '
            f'{TAMANHO_CAPA[0]}x{TAMANHO_CAPA[1]}.'
        )
    if not capa_alt:
        raise CommandError('"capa_alt" é obrigatório quando há capa (descrição da imagem).')
    if not capa_credito:
        raise CommandError('"capa_credito" é obrigatório quando há capa, ex.: Foto: Fulano / Unsplash.')
    if len(capa_alt) > 200:
        raise CommandError(f'"capa_alt" tem {len(capa_alt)} caracteres, o máximo é 200.')
    if len(capa_credito) > 300:
        raise CommandError(f'"capa_credito" tem {len(capa_credito)} caracteres, o máximo é 300.')


class Command(BaseCommand):
    help = (
        'Cria um Artigo como rascunho a partir de um arquivo JSON com os '
        'campos titulo, resumo, corpo (HTML) e categoria, e os opcionais capa, '
        'capa_alt, capa_credito e com_apoio_ia. Usado pela skill '
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

        capa = dados.get('capa') or ''
        capa_alt = dados.get('capa_alt') or ''
        capa_credito = dados.get('capa_credito') or ''
        if capa:
            validar_capa(capa, capa_alt, capa_credito)
        com_apoio_ia = dados.get('com_apoio_ia', False)
        if not isinstance(com_apoio_ia, bool):
            raise CommandError('"com_apoio_ia" precisa ser true ou false.')

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
            capa=capa,
            capa_alt=capa_alt,
            capa_credito=capa_credito,
            com_apoio_ia=com_apoio_ia,
        )

        self.stdout.write(self.style.SUCCESS(
            f'Rascunho criado: "{artigo.titulo}" (slug={artigo.slug}).\n'
            f'Revise e publique em /admin/conteudo/artigo/{artigo.pk}/change/'
        ))

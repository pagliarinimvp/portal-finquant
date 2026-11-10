from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db.migrations.loader import MigrationLoader
from django.utils import timezone

from conteudo.models import Artigo

PASTA_MIGRACOES = Path(__file__).resolve().parents[2] / 'migrations'

CAMPOS = ('titulo', 'slug', 'resumo', 'corpo', 'categoria',
          'capa', 'capa_alt', 'capa_credito', 'com_apoio_ia')

MODELO = '''# Gerada por `manage.py exportar_artigo_migracao {slug}`.
# Leva à produção o rascunho criado e revisado no banco local: o `migrate`
# do deploy cria o artigo como rascunho, e o autor o publica pelo Admin.
from django.db import migrations

ARTIGO = {{
{campos}
}}


def importar_artigo(apps, schema_editor):
    Artigo = apps.get_model('conteudo', 'Artigo')
    Artigo.objects.get_or_create(slug=ARTIGO['slug'], defaults=ARTIGO)


def remover_artigo(apps, schema_editor):
    Artigo = apps.get_model('conteudo', 'Artigo')
    Artigo.objects.filter(slug=ARTIGO['slug']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('conteudo', {folha!r}),
    ]

    operations = [
        migrations.RunPython(importar_artigo, remover_artigo),
    ]
'''


MODELO_SUBSTITUICAO = '''# Gerada por `manage.py exportar_artigo_migracao {slug} --substituir {antigo}`.
# Leva à produção a versão nova de um artigo no lugar da antiga: o artigo
# {antigo!r} recebe o conteúdo de {slug!r} e mantém endereço, status e data de
# publicação. Se já estiver publicado, o texto novo vai ao ar com o deploy.
from django.db import migrations

SLUG_ANTIGO = {antigo!r}
REVISADO_EM = {revisado_em!r}

NOVO = {{
{campos}
}}

ANTERIOR = {{
{anterior}
}}


def substituir_artigo(apps, schema_editor):
    Artigo = apps.get_model('conteudo', 'Artigo')
    artigo = Artigo.objects.filter(slug=SLUG_ANTIGO).first()
    if artigo is None:
        # Sem a versão antiga no banco, a nova entra como rascunho, com o próprio slug.
        Artigo.objects.get_or_create(slug=NOVO['slug'], defaults=NOVO)
        return
    for campo, valor in NOVO.items():
        if campo not in ('slug', 'status'):
            setattr(artigo, campo, valor)
    artigo.revisado_em = REVISADO_EM
    artigo.save()


def desfazer_substituicao(apps, schema_editor):
    Artigo = apps.get_model('conteudo', 'Artigo')
    artigo = Artigo.objects.filter(slug=SLUG_ANTIGO).first()
    if artigo is None:
        Artigo.objects.filter(slug=NOVO['slug'], status='RASCUNHO').delete()
        return
    for campo, valor in ANTERIOR.items():
        setattr(artigo, campo, valor)
    artigo.save()


class Migration(migrations.Migration):

    dependencies = [
        ('conteudo', {folha!r}),
    ]

    operations = [
        migrations.RunPython(substituir_artigo, desfazer_substituicao),
    ]
'''


def _linhas(valores):
    return '\n'.join(f'    {campo!r}: {valor!r},' for campo, valor in valores.items())


def folha_do_conteudo():
    grafo = MigrationLoader(None, ignore_no_migrations=True).graph
    folhas = [nome for app, nome in grafo.leaf_nodes() if app == 'conteudo']
    if len(folhas) != 1:
        raise CommandError(
            f'O app conteudo tem {len(folhas)} migrações finais ({", ".join(folhas)}); '
            'resolva com `makemigrations --merge` antes de exportar.'
        )
    return folhas[0]


class Command(BaseCommand):
    help = (
        'Gera uma migração de dados que cria em produção, como rascunho, um '
        'artigo do banco local. Usado pela skill formatar-artigo depois que o '
        'autor aprova o rascunho e pede o commit.'
    )

    def add_arguments(self, parser):
        parser.add_argument('slug', help='Slug do artigo no banco local.')
        parser.add_argument('--pasta', help='Onde gravar (padrão: conteudo/migrations).')
        parser.add_argument(
            '--substituir', metavar='SLUG_ANTIGO',
            help='Em vez de criar um artigo novo, põe este no lugar do artigo SLUG_ANTIGO, '
                 'que mantém endereço, status e data de publicação e ganha "Atualizado em".',
        )

    def handle(self, *args, **options):
        slug = options['slug']
        artigo = Artigo.objects.filter(slug=slug).first()
        if artigo is None:
            raise CommandError(f'Nenhum artigo com o slug {slug!r} no banco local.')

        folha = folha_do_conteudo()
        numero = int(folha.split('_', 1)[0]) + 1

        valores = {campo: getattr(artigo, campo) for campo in CAMPOS}
        valores['status'] = Artigo.Status.RASCUNHO.value

        antigo = options.get('substituir')
        if antigo:
            if antigo == slug:
                raise CommandError('Não dá para substituir um artigo por ele mesmo.')
            anterior = Artigo.objects.filter(slug=antigo).first()
            if anterior is None:
                raise CommandError(f'Nenhum artigo com o slug {antigo!r} no banco local.')
            valores_anteriores = {c: getattr(anterior, c) for c in CAMPOS if c != 'slug'}
            revisado = anterior.revisado_em
            valores_anteriores['revisado_em'] = revisado.isoformat() if revisado else None
            nome = f'{numero:04d}_substitui_artigo_{antigo.replace("-", "_")[:40]}.py'
            conteudo = MODELO_SUBSTITUICAO.format(
                slug=slug, antigo=antigo, revisado_em=timezone.localdate().isoformat(),
                campos=_linhas(valores), anterior=_linhas(valores_anteriores), folha=folha)
        else:
            nome = f'{numero:04d}_importa_artigo_{slug.replace("-", "_")[:40]}.py'
            conteudo = MODELO.format(slug=slug, campos=_linhas(valores), folha=folha)

        destino = Path(options['pasta'] or PASTA_MIGRACOES) / nome
        destino.write_bytes(conteudo.encode('utf-8'))
        self.stdout.write(self.style.SUCCESS(f'Migração gravada em {destino}'))

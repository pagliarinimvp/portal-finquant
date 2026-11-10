from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db.migrations.loader import MigrationLoader

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

    def handle(self, *args, **options):
        slug = options['slug']
        artigo = Artigo.objects.filter(slug=slug).first()
        if artigo is None:
            raise CommandError(f'Nenhum artigo com o slug {slug!r} no banco local.')

        folha = folha_do_conteudo()
        numero = int(folha.split('_', 1)[0]) + 1
        nome = f'{numero:04d}_importa_artigo_{slug.replace("-", "_")[:40]}.py'

        valores = {campo: getattr(artigo, campo) for campo in CAMPOS}
        valores['status'] = Artigo.Status.RASCUNHO.value
        campos = '\n'.join(f'    {campo!r}: {valor!r},' for campo, valor in valores.items())

        destino = Path(options['pasta'] or PASTA_MIGRACOES) / nome
        destino.write_bytes(MODELO.format(slug=slug, campos=campos, folha=folha).encode('utf-8'))
        self.stdout.write(self.style.SUCCESS(f'Migração gravada em {destino}'))

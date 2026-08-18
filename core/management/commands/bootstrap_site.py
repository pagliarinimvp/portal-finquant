import os

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        'Ajusta o domínio do registro Site (SITE_ID) a partir da variável de '
        'ambiente SITE_DOMAIN, se ela estiver definida. Sem isso, o Site fica '
        'com o valor padrão "example.com" do Django, e recursos que dependem '
        'dele — como o "Ver no site" do admin e o login social — apontam para '
        'o domínio errado. Seguro para rodar em todo deploy: fica inerte se a '
        'variável não estiver definida.'
    )

    def handle(self, **options):
        domain = os.environ.get('SITE_DOMAIN')

        if not domain:
            self.stdout.write('SITE_DOMAIN não definida — nada a fazer.')
            return

        site, criado = Site.objects.update_or_create(
            id=settings.SITE_ID,
            defaults={'domain': domain, 'name': domain},
        )
        acao = 'criado' if criado else 'atualizado'
        self.stdout.write(self.style.SUCCESS(f'Site {acao}: domain="{site.domain}".'))

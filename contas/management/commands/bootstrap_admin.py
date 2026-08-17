import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        'Cria o superusuário a partir das variáveis de ambiente '
        'DJANGO_SUPERUSER_USERNAME/EMAIL/PASSWORD, se ele ainda não existir. '
        'Seguro para rodar em todo deploy: fica inerte se as variáveis não '
        'estiverem definidas ou se o usuário já existir (nunca sobrescreve senha).'
    )

    def handle(self, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if not username or not password:
            self.stdout.write('DJANGO_SUPERUSER_USERNAME/PASSWORD não definidos — nada a fazer.')
            return

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write(f'Usuário "{username}" já existe — nada a fazer.')
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f'Superusuário "{username}" criado.'))

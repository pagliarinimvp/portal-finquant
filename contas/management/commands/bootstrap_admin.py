import os

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        'Cria o superusuário a partir das variáveis de ambiente '
        'DJANGO_SUPERUSER_USERNAME/EMAIL/PASSWORD, se ele ainda não existir, e '
        'garante que ele tenha uma EmailAddress verificada do allauth (sem ela, '
        'o primeiro login social com o mesmo e-mail apaga a senha local via '
        'wipe_password() — foi o que aconteceu em produção em 19/08/2026, porque '
        'esse comando roda depois da migração que protege contas existentes). Se '
        'a senha já estiver inutilizável por esse motivo, restaura a partir de '
        'DJANGO_SUPERUSER_PASSWORD. Seguro para rodar em todo deploy: fica '
        'inerte se as variáveis não estiverem definidas, e nunca sobrescreve '
        'uma senha que já está utilizável.'
    )

    def handle(self, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if not username or not password:
            self.stdout.write('DJANGO_SUPERUSER_USERNAME/PASSWORD não definidos — nada a fazer.')
            return

        User = get_user_model()
        user = User.objects.filter(username=username).first()

        if user is None:
            user = User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Superusuário "{username}" criado.'))
        elif not user.has_usable_password():
            user.set_password(password)
            user.save(update_fields=['password'])
            self.stdout.write(self.style.WARNING(f'Senha de "{username}" estava inutilizável — restaurada.'))
        else:
            self.stdout.write(f'Usuário "{username}" já existe — nada a fazer.')

        if user.email:
            EmailAddress.objects.get_or_create(
                user=user,
                email=user.email,
                defaults={'verified': True, 'primary': True},
            )

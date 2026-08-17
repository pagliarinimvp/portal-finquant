from django.db import migrations


def marcar_emails_existentes_como_verificados(apps, schema_editor):
    """Evita que o allauth invalide a senha local de usuarios existentes
    no primeiro login social: sem uma EmailAddress verificada, o
    SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT chama wipe_password()
    ao conectar automaticamente por e-mail."""
    User = apps.get_model('auth', 'User')
    EmailAddress = apps.get_model('account', 'EmailAddress')
    for usuario in User.objects.exclude(email=''):
        EmailAddress.objects.get_or_create(
            user=usuario,
            email=usuario.email,
            defaults={'verified': True, 'primary': True},
        )


def reverter(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('account', '0009_emailaddress_unique_primary_email'),
    ]

    operations = [
        migrations.RunPython(marcar_emails_existentes_como_verificados, reverter),
    ]

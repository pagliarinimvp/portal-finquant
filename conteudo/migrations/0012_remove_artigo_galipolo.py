# Remove o artigo do Galípolo (pedido do autor, 10/11/2026). Ele estava publicado
# desde 28/08/2026; depois do deploy, o endereço dá "página não encontrada".
# As migrações 0004, 0006 e 0011 continuam, porque o histórico não se reescreve:
# esta roda depois delas e apaga o artigo.
from django.db import migrations

SLUG = 'galipolo-defende-juros-restritivos-para-reequilibrar-oferta-e-demanda-no-brasil'


def remover(apps, schema_editor):
    Artigo = apps.get_model('conteudo', 'Artigo')
    artigo = Artigo.objects.filter(slug=SLUG).first()
    if artigo is None:
        return
    # As respostas de "Este artigo te ajudou?" protegem o artigo (PROTECT).
    # No dia da remoção ele não tinha nenhuma; se tiver, saem junto com ele.
    AvaliacaoArtigo = apps.get_model('avaliacoes', 'AvaliacaoArtigo')
    AvaliacaoArtigo.objects.filter(artigo=artigo).delete()
    artigo.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('conteudo', '0011_substitui_artigo_galipolo_defende_juros_restritivos_para_'),
        ('avaliacoes', '0008_avaliacao_artigo'),
    ]

    operations = [
        # Desfazer não recria o artigo.
        migrations.RunPython(remover, migrations.RunPython.noop),
    ]

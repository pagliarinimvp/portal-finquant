from django.db import migrations

ARTIGOS_EXEMPLO = [
    {
        'titulo': 'O que são finanças quantitativas?',
        'slug': 'o-que-sao-financas-quantitativas',
        'resumo': 'Um panorama simples sobre como matemática e dados são usados para tomar decisões de investimento.',
        'corpo': (
            'Finanças quantitativas são a área que usa matemática, estatística e dados '
            'para entender o comportamento de investimentos e apoiar decisões financeiras.\n\n'
            'Em vez de decidir "no feeling", investidores quantitativos analisam números: '
            'histórico de preços, risco, retorno esperado e correlações entre ativos. '
            'Neste portal, vamos explicar esses conceitos passo a passo, sem exigir que você '
            'já saiba matemática avançada.'
        ),
        'categoria': 'FUNDAMENTOS',
    },
    {
        'titulo': 'Renda fixa: como funciona na prática',
        'slug': 'renda-fixa-como-funciona-na-pratica',
        'resumo': 'Entenda o que são títulos de renda fixa e por que costumam ser a porta de entrada dos investidores.',
        'corpo': (
            'Renda fixa é uma modalidade de investimento em que as regras de remuneração '
            'são definidas no momento da aplicação: você "empresta" dinheiro (para o governo, '
            'um banco ou uma empresa) e recebe de volta com juros combinados previamente.\n\n'
            'É considerada uma opção mais previsível que a renda variável, por isso costuma '
            'ser o primeiro passo de quem está começando a investir.'
        ),
        'categoria': 'RENDA_FIXA',
    },
    {
        'titulo': 'Renda variável: o que são ações',
        'slug': 'renda-variavel-o-que-sao-acoes',
        'resumo': 'Uma introdução ao mercado de ações para quem nunca investiu em renda variável.',
        'corpo': (
            'Uma ação representa uma pequena fração da propriedade de uma empresa. Ao comprar '
            'ações, você passa a ser sócio(a) daquele negócio e pode ganhar dinheiro de duas formas: '
            'com a valorização do preço da ação ao longo do tempo, ou com o recebimento de dividendos '
            '(parte do lucro distribuído aos acionistas).\n\n'
            'Diferente da renda fixa, o retorno da renda variável não é garantido — daí o nome.'
        ),
        'categoria': 'RENDA_VARIAVEL',
    },
]


def criar_artigos_exemplo(apps, schema_editor):
    Artigo = apps.get_model('conteudo', 'Artigo')
    for dados in ARTIGOS_EXEMPLO:
        Artigo.objects.get_or_create(slug=dados['slug'], defaults=dados)


def remover_artigos_exemplo(apps, schema_editor):
    Artigo = apps.get_model('conteudo', 'Artigo')
    slugs = [dados['slug'] for dados in ARTIGOS_EXEMPLO]
    Artigo.objects.filter(slug__in=slugs).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('conteudo', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(criar_artigos_exemplo, remover_artigos_exemplo),
    ]

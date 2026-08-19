from django.db import migrations

ARTIGO = {
    "titulo": 'Galípolo defende juros restritivos para reequilibrar oferta e demanda no Brasil',
    "slug": 'galipolo-defende-juros-restritivos-para-reequilibrar-oferta-e-demanda-no-brasil',
    "resumo": 'Presidente do Banco Central afirma que a Selic elevada reflete fatores internos, não externos. Boletim Focus mantém projeções estáveis para inflação, juros, PIB e dólar em 2026.',
    "corpo": '<p>O presidente do Banco Central, Gabriel Galípolo, afirmou durante a 27ª Conferência Anual do Santander, em São Paulo, no dia 17 de agosto de 2026, que a manutenção da Selic em patamar elevado decorre principalmente de fatores domésticos, e não de pressões externas.</p><h2>Selic em patamar restritivo</h2><p>Na última reunião do Comitê de Política Monetária (Copom), realizada em 5 de agosto, o Banco Central reduziu a taxa básica de juros para 14% ao ano. Segundo Galípolo, o nível ainda restritivo é resultado de uma economia que opera em pleno emprego, com crescimento puxado pelo consumo.</p><p>"A demanda superou a capacidade de oferta do país, gerando pressão inflacionária direta", disse o presidente do BC. Ele completou: "o mandato é conseguir reequilibrar oferta e demanda, e é por isso que a gente coloca a taxa de juros em um patamar restritivo."</p><h3>Produtividade e crédito</h3><p>Galípolo alertou que o crescimento sustentado da economia depende de ganhos de produtividade. Sem esse avanço, segundo ele, o país segue "batendo no muro" da inflação. O presidente do BC também classificou como preocupante o avanço da inadimplência, destacando que parte dos brasileiros recorre a linhas de crédito mais caras, como o cartão rotativo, em vez de modalidades com garantias.</p><h2>Mercado mantém projeções estáveis no Focus</h2><p>O Boletim Focus, divulgado pelo Banco Central na segunda-feira, 17 de agosto, mostrou que as expectativas do mercado financeiro para os principais indicadores de 2026 permaneceram estáveis:</p><ul><li>Inflação (IPCA): 5,02% ao ano</li><li>Selic: 13,75% ao ano</li><li>PIB: crescimento de 1,98%</li><li>Dólar: R$ 5,20</li></ul><p>Para 2027, as projeções tiveram ajustes pontuais: a expectativa de IPCA subiu de 4,22% para 4,24%, a de PIB caiu de 1,52% para 1,50%, o dólar passou de R$ 5,28 para R$ 5,29, e a Selic projetada permaneceu em 12% ao ano.</p><p>A projeção de inflação para 2026 segue acima da meta do Banco Central. Ainda assim, o boletim aponta que a inflação "perdeu fôlego" por quatro meses consecutivos — em julho, o índice oficial medido pelo IBGE ficou em 0,07%.</p><h3>Fontes</h3><ul><li><a href="https://www.seudinheiro.com/2026/economia/galipolo-selic-deve-seguir-restritiva-para-reequilibrar-oferta-e-demanda-ccgg/">Selic continua alta por fatores internos, alerta Galípolo</a></li><li><a href="https://borainvestir.b3.com.br/noticias/focus-mercado-mantem-estaveis-projecoes-para-inflacao-juros-pib-e-dolar/">Focus: mercado mantém estáveis projeções para inflação, juros, PIB e dólar</a></li></ul>',
    "categoria": 'RENDA_FIXA',
    "status": 'RASCUNHO',
}


def importar_artigo(apps, schema_editor):
    Artigo = apps.get_model("conteudo", "Artigo")
    Artigo.objects.get_or_create(slug=ARTIGO["slug"], defaults=ARTIGO)


def remover_artigo(apps, schema_editor):
    Artigo = apps.get_model("conteudo", "Artigo")
    Artigo.objects.filter(slug=ARTIGO["slug"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("conteudo", "0003_artigo_status_alter_artigo_corpo"),
    ]

    operations = [
        migrations.RunPython(importar_artigo, remover_artigo),
    ]

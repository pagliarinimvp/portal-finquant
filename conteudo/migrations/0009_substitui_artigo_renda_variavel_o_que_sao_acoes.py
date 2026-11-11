# Gerada por `manage.py exportar_artigo_migracao acoes-o-que-sao-como-voce-ganha-e-perde-e-quanto-paga-de-imposto --substituir renda-variavel-o-que-sao-acoes`.
# Leva à produção a versão nova de um artigo no lugar da antiga: o artigo
# 'renda-variavel-o-que-sao-acoes' recebe o conteúdo de 'acoes-o-que-sao-como-voce-ganha-e-perde-e-quanto-paga-de-imposto' e mantém endereço, status e data de
# publicação. Se já estiver publicado, o texto novo vai ao ar com o deploy.
from django.db import migrations

SLUG_ANTIGO = 'renda-variavel-o-que-sao-acoes'
REVISADO_EM = '2026-11-10'

NOVO = {
    'titulo': 'Ações: o que são, como você ganha (e perde) e quanto paga de imposto',
    'slug': 'acoes-o-que-sao-como-voce-ganha-e-perde-e-quanto-paga-de-imposto',
    'resumo': 'Ter uma ação é ser dono de um pedaço de uma empresa. Entenda a diferença entre ON e PN, os dividendos, os juros sobre capital próprio e as regras de imposto que valem desde 2026.',
    'corpo': '<aside class="fq-em-30s"><h4>Em 30 segundos</h4><ul>\n<li>Uma ação é uma fração do capital de uma empresa: quem compra vira sócio dela.</li>\n<li>As ordinárias (ON, código terminado em 3) dão direito a voto; as preferenciais (PN, terminado em 4) costumam não votar, mas têm prioridade no recebimento de dividendos.</li>\n<li>Você pode ganhar com a valorização da ação, com dividendos e com juros sobre capital próprio. E pode perder, porque nada disso é garantido.</li>\n<li>Desde 01/01/2026, os juros sobre capital próprio têm 17,5% de imposto na fonte, e dividendos acima de R$ 50 mil no mês, pagos pela mesma empresa, têm 10% retidos.</li>\n</ul></aside>\n<aside class="fq-sumario"><h4>Neste artigo</h4><ol>\n<li><a href="#o-que-e">O que é uma ação?</a></li>\n<li><a href="#on-e-pn">ON e PN: o que muda?</a></li>\n<li><a href="#como-ganha">Como se ganha com ações?</a></li>\n<li><a href="#imposto">O que mudou no imposto em 2026?</a></li>\n<li><a href="#risco">Qual é o risco?</a></li>\n</ol></aside>\n<p>Comprar uma ação é comprar um pedacinho de uma empresa. Quem tem ações é sócio do negócio: participa dos lucros quando eles são distribuídos e sente no bolso quando o preço da ação cai. Este artigo explica os tipos de ação, as formas de ganhar dinheiro com elas e as regras de imposto que passaram a valer em 2026.</p>\n<h2 id="o-que-e">O que é uma ação?</h2>\n<p>Pela Lei das S.A. (Lei 6.404, de 1976), o capital de uma <strong>sociedade anônima</strong> é dividido em ações. Cada ação é uma fração desse capital, e a responsabilidade do acionista fica limitada ao preço de emissão das ações que ele tem.</p>\n<p>As empresas de capital aberto têm suas ações negociadas na <strong>B3</strong>, a bolsa de valores brasileira. Para comprar, você precisa de uma conta numa corretora ou num banco que dê acesso à bolsa.</p>\n<h2 id="on-e-pn">ON e PN: o que muda?</h2>\n<p>A lei divide as ações em ordinárias, preferenciais e de fruição. As duas primeiras são as que você vai encontrar na bolsa:</p>\n<ul>\n<li><strong>Ordinárias (ON):</strong> dão direito a voto nas assembleias da empresa. O código costuma terminar em 3 (por exemplo, PETR3).</li>\n<li><strong>Preferenciais (PN):</strong> em geral não dão direito a voto, mas têm vantagens financeiras, como prioridade no recebimento de dividendos e de juros sobre capital próprio. O código costuma terminar em 4 (por exemplo, PETR4).</li>\n</ul>\n<p>As vantagens exatas das PN de cada empresa estão no estatuto social dela.</p>\n<h2 id="como-ganha">Como se ganha com ações?</h2>\n<p>Há três caminhos:</p>\n<ul>\n<li><strong>Valorização:</strong> você compra a ação a um preço e vende mais caro. O ganho só existe de verdade na venda.</li>\n<li><strong>Dividendos:</strong> parte do lucro que a empresa distribui aos acionistas, em dinheiro.</li>\n<li><strong>Juros sobre capital próprio (JCP):</strong> outra forma de a empresa remunerar os acionistas, com regras de imposto diferentes das dos dividendos.</li>\n</ul>\n<h2 id="imposto">O que mudou no imposto em 2026?</h2>\n<p>Duas leis mudaram as regras a partir de 01/01/2026:</p>\n<ul>\n<li><strong>JCP:</strong> o imposto de renda retido na fonte subiu de 15% para 17,5% (Lei Complementar 224, de 2025).</li>\n<li><strong>Dividendos:</strong> continuam sem retenção na maioria dos casos. Mas, quando a mesma empresa paga mais de R$ 50 mil em um mês à mesma pessoa física, 10% são retidos na fonte sobre o valor total pago (Lei 15.270, de 2025).</li>\n</ul>\n<aside class="fq-na-pratica"><h4>Na prática</h4>\n<p><strong>JCP:</strong> a empresa declara R$ 100,00 de JCP para você. São retidos 17,5% (R$ 17,50) e você recebe R$ 82,50.</p>\n<p><strong>Dividendos pequenos:</strong> você recebe R$ 300,00 de dividendos de uma empresa no mês. Como está abaixo de R$ 50 mil, não há retenção.</p>\n<p><strong>Dividendos acima do limite:</strong> uma mesma empresa paga R$ 60.000,00 a uma pessoa no mês. A retenção é de 10% sobre o total: R$ 6.000,00.</p>\n</aside>\n<p>O lucro na venda das ações tem regras próprias de imposto, que ficam para outro artigo.</p>\n<h2 id="risco">Qual é o risco?</h2>\n<p>Ação é <strong>renda variável</strong>: não existe rendimento combinado. O preço sobe e desce todos os dias, a empresa pode ter prejuízo e deixar de pagar dividendos, e você pode vender por menos do que pagou. Ao contrário de CDB e poupança, ações não têm garantia do FGC.</p><aside class="fq-glossario"><h4>Glossário</h4><dl>\n<dt>Ação</dt><dd>Fração do capital de uma sociedade anônima.</dd>\n<dt>Sociedade anônima</dt><dd>Empresa cujo capital é dividido em ações.</dd>\n<dt>B3</dt><dd>A bolsa de valores do Brasil, onde as ações são negociadas.</dd>\n<dt>Ação ordinária (ON)</dt><dd>Dá direito a voto nas assembleias. Código terminado em 3.</dd>\n<dt>Ação preferencial (PN)</dt><dd>Em geral sem voto, com prioridade em dividendos e JCP. Código terminado em 4.</dd>\n<dt>Dividendos</dt><dd>Parte do lucro distribuída aos acionistas em dinheiro.</dd>\n<dt>Juros sobre capital próprio (JCP)</dt><dd>Forma de remunerar o acionista com 17,5% de imposto retido na fonte desde 2026.</dd>\n<dt>Renda variável</dt><dd>Investimento cujo retorno não é conhecido de antemão.</dd>\n</dl></aside>\n<h3>Para saber mais</h3>\n<p><a href="/estudo-caso/">Análise de ações: teste uma regra de compra e venda em ações do Ibovespa</a></p>\n<h3>Fontes</h3>\n<ol>\n<li>Presidência da República. <a href="https://www.planalto.gov.br/ccivil_03/leis/l6404consol.htm">Lei nº 6.404, de 15/12/1976 (Lei das S.A.), arts. 1º e 15</a>. Consulta em 10/11/2026.</li>\n<li>Bora Investir (B3). <a href="https://borainvestir.b3.com.br/glossario/acao-preferencial/">Ação preferencial: glossário</a>. Consulta em 10/11/2026.</li>\n<li>Presidência da República. <a href="https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/lei/L15270.htm">Lei nº 15.270, de 26/11/2025 (art. 6º-A da Lei 9.250)</a>. Consulta em 10/11/2026.</li>\n<li>Presidência da República. <a href="https://www.planalto.gov.br/ccivil_03/leis/l9249.htm">Lei nº 9.249, de 26/12/1995, art. 9º, § 2º, com a redação da Lei Complementar nº 224, de 26/12/2025</a>. Consulta em 10/11/2026.</li>\n</ol>',
    'categoria': 'RENDA_VARIAVEL',
    'capa': 'img/artigos/acoes-o-que-sao-como-voce-ganha-e-perde-e-quanto-paga-de-imposto/capa.jpg',
    'capa_alt': 'Mesa de trabalho com monitor, notebook, tablet e celular mostrando gráficos de preços, e uma calculadora.',
    'capa_credito': 'Foto: Jakub Żerdzicki / Unsplash',
    'com_apoio_ia': True,
    'status': 'RASCUNHO',
}

ANTERIOR = {
    'titulo': 'Renda variável: o que são ações',
    'resumo': 'Uma introdução ao mercado de ações para quem nunca investiu em renda variável.',
    'corpo': 'Uma ação representa uma pequena fração da propriedade de uma empresa. Ao comprar ações, você passa a ser sócio(a) daquele negócio e pode ganhar dinheiro de duas formas: com a valorização do preço da ação ao longo do tempo, ou com o recebimento de dividendos (parte do lucro distribuído aos acionistas).\n\nDiferente da renda fixa, o retorno da renda variável não é garantido — daí o nome.',
    'categoria': 'RENDA_VARIAVEL',
    'capa': '',
    'capa_alt': '',
    'capa_credito': '',
    'com_apoio_ia': False,
    'revisado_em': None,
}


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
        ('conteudo', '0008_substitui_artigo_o_que_sao_financas_quantitativas'),
    ]

    operations = [
        migrations.RunPython(substituir_artigo, desfazer_substituicao),
    ]

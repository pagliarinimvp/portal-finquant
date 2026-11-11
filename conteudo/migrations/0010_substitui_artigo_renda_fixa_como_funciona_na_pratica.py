# Gerada por `manage.py exportar_artigo_migracao renda-fixa-como-funciona-quem-garante-e-quanto-rende --substituir renda-fixa-como-funciona-na-pratica`.
# Leva à produção a versão nova de um artigo no lugar da antiga: o artigo
# 'renda-fixa-como-funciona-na-pratica' recebe o conteúdo de 'renda-fixa-como-funciona-quem-garante-e-quanto-rende' e mantém endereço, status e data de
# publicação. Se já estiver publicado, o texto novo vai ao ar com o deploy.
from django.db import migrations

SLUG_ANTIGO = 'renda-fixa-como-funciona-na-pratica'
REVISADO_EM = '2026-11-10'

NOVO = {
    'titulo': 'Renda fixa: como funciona, quem garante e quanto rende',
    'slug': 'renda-fixa-como-funciona-quem-garante-e-quanto-rende',
    'resumo': 'Na renda fixa, você empresta dinheiro ao governo, a um banco ou a uma empresa e sabe de antemão como ele vai render. Veja os tipos, as garantias e o imposto.',
    'corpo': '<aside class="fq-em-30s"><h4>Em 30 segundos</h4><ul>\n<li>Na renda fixa, você empresta dinheiro ao governo, a um banco ou a uma empresa, e a regra de remuneração fica combinada no momento da aplicação.</li>\n<li>Os títulos do Tesouro Direto são garantidos pelo Tesouro Nacional. CDB, LCI, LCA e poupança têm a garantia do FGC, de até R$ 250 mil por CPF em cada instituição.</li>\n<li>O imposto de renda diminui com o tempo: vai de 22,5% (até 180 dias) a 15% (mais de 720 dias). LCI e LCA são isentas para pessoa física.</li>\n<li>"Fixa" não quer dizer sem risco: quem vende um título antes do vencimento recebe o preço do dia, que pode ser maior ou menor que o combinado.</li>\n</ul></aside>\n<aside class="fq-sumario"><h4>Neste artigo</h4><ol>\n<li><a href="#o-que-e">O que é renda fixa?</a></li>\n<li><a href="#tipos">Quais são os tipos?</a></li>\n<li><a href="#quem-garante">Quem garante o meu dinheiro?</a></li>\n<li><a href="#imposto">Quanto de imposto eu pago?</a></li>\n<li><a href="#tem-risco">Renda fixa tem risco?</a></li>\n</ol></aside>\n<p>Renda fixa é o investimento em que você empresta dinheiro a alguém (o governo, um banco ou uma empresa) e já sabe, no dia da aplicação, como ele vai render. É por onde muita gente começa a investir, e entender três pontos ajuda muito: quem está do outro lado, quem garante e quanto vai para o imposto.</p>\n<h2 id="o-que-e">O que é renda fixa?</h2>\n<p>Pense num empréstimo ao contrário: em vez de você pegar dinheiro emprestado e pagar juros, é você quem empresta e recebe os juros. Quem pega o dinheiro é o <strong>emissor</strong> do título.</p>\n<p>A remuneração pode ser combinada de três jeitos:</p>\n<ul>\n<li><strong>Prefixada:</strong> a taxa é fixa desde o início (por exemplo, 12% ao ano).</li>\n<li><strong>Pós-fixada:</strong> o rendimento acompanha um índice de juros, como a Selic.</li>\n<li><strong>Atrelada à inflação:</strong> rende a inflação do período mais uma taxa fixa.</li>\n</ul>\n<h2 id="tipos">Quais são os tipos?</h2>\n<p>Os mais conhecidos de quem está começando:</p>\n<ul>\n<li><strong>Tesouro Direto:</strong> programa do Tesouro Nacional, em parceria com a B3, que vende títulos públicos a pessoas físicas desde 2002, sem valor mínimo de investimento. Os principais são o Tesouro Selic (pós-fixado), o Tesouro Prefixado e o Tesouro IPCA+ (atrelado à inflação).</li>\n<li><strong>CDB:</strong> Certificado de Depósito Bancário. Você empresta dinheiro a um banco.</li>\n<li><strong>LCI e LCA:</strong> Letras de Crédito Imobiliário e do Agronegócio. Também emitidas por bancos, com o dinheiro destinado a esses setores.</li>\n<li><strong>Poupança:</strong> a conta mais tradicional, também garantida pelo FGC.</li>\n</ul>\n<h2 id="quem-garante">Quem garante o meu dinheiro?</h2>\n<p>Depende de quem é o emissor:</p>\n<ul>\n<li><strong>Títulos do Tesouro Direto:</strong> garantidos pelo Tesouro Nacional, ou seja, pelo governo federal.</li>\n<li><strong>CDB, LCI, LCA e poupança:</strong> garantidos pelo <strong>FGC</strong>, o Fundo Garantidor de Créditos, se o banco quebrar. O limite é de R$ 250 mil por CPF em cada instituição ou conglomerado financeiro, com um teto de R$ 1 milhão a cada quatro anos, somando todos os pagamentos que a pessoa receber do FGC.</li>\n</ul>\n<h2 id="imposto">Quanto de imposto eu pago?</h2>\n<p>Na maioria dos títulos de renda fixa, como Tesouro Direto e CDB, o imposto de renda segue a <strong>tabela regressiva</strong>: quanto mais tempo o dinheiro fica aplicado, menor a alíquota. O imposto incide só sobre o rendimento, não sobre o valor que você aplicou.</p>\n<ul>\n<li>Até 180 dias: 22,5%</li>\n<li>De 181 a 360 dias: 20%</li>\n<li>De 361 a 720 dias: 17,5%</li>\n<li>Mais de 720 dias: 15%</li>\n</ul>\n<p>A tabela está na Lei 11.033, de 2004. Uma medida provisória de 2025 (MP 1.303) propôs trocá-la por uma alíquota única, mas perdeu a validade, e a tabela continua em vigor. A mesma lei isenta do imposto de renda a pessoa física que investe em LCI e LCA.</p>\n<aside class="fq-na-pratica"><h4>Na prática</h4>\n<p>Imagine R$ 10.000 aplicados por um ano (365 dias) num título que rende 13,75% ao ano, o valor da Selic em 04/11/2026.</p>\n<p>Rendimento: R$ 10.000 × 13,75% = R$ 1.375,00.</p>\n<p>Como o prazo ficou entre 361 e 720 dias, a alíquota é de 17,5%: R$ 1.375,00 × 17,5% = R$ 240,63 de imposto (arredondado).</p>\n<p>Sobram R$ 1.134,37 de rendimento líquido. A conta é simplificada e não inclui taxas.</p>\n<p><a href="/simuladores/juros-compostos/?valor_inicial=10000&amp;aporte_mensal=0&amp;taxa_mensal=13.75&amp;periodo_taxa=anual&amp;periodo_meses=12">Refaça a conta no simulador</a> e troque os valores pelos seus.</p>\n</aside>\n<h2 id="tem-risco">Renda fixa tem risco?</h2>\n<p>Tem, e é bom conhecer dois:</p>\n<ul>\n<li><strong>Venda antes do vencimento:</strong> o Tesouro Nacional garante a rentabilidade combinada para quem fica com o título até o vencimento. Quem vende antes recebe o valor de mercado daquele dia, que pode ser maior ou menor do que o combinado. Esse sobe e desce do preço se chama <strong>marcação a mercado</strong>.</li>\n<li><strong>Risco do emissor:</strong> se o banco quebrar, o FGC cobre até o limite. O que passar do limite pode não ser devolvido.</li>\n</ul>\n<aside class="fq-glossario"><h4>Glossário</h4><dl>\n<dt>Emissor</dt><dd>Quem recebe o dinheiro emprestado e paga os juros: o governo, um banco ou uma empresa.</dd>\n<dt>Prefixado</dt><dd>Título com taxa de juros definida no momento da aplicação.</dd>\n<dt>Pós-fixado</dt><dd>Título cujo rendimento acompanha um índice, como a Selic.</dd>\n<dt>Selic</dt><dd>Taxa básica de juros da economia, definida pelo Copom, do Banco Central.</dd>\n<dt>CDB</dt><dd>Certificado de Depósito Bancário: empréstimo do investidor a um banco.</dd>\n<dt>LCI e LCA</dt><dd>Letras de Crédito Imobiliário e do Agronegócio, emitidas por bancos e isentas de IR para pessoa física.</dd>\n<dt>FGC</dt><dd>Fundo Garantidor de Créditos: devolve até R$ 250 mil por CPF e instituição se um banco associado quebrar.</dd>\n<dt>Tabela regressiva</dt><dd>Regra do imposto de renda em que a alíquota cai conforme o prazo da aplicação.</dd>\n<dt>Marcação a mercado</dt><dd>Atualização diária do preço de um título conforme as condições do mercado.</dd>\n</dl></aside>\n<h3>Para saber mais</h3>\n<p><a href="/simuladores/juros-compostos/">Simulador de juros compostos</a></p>\n<p><a href="/simuladores/meta-financeira/">Calculadora de meta financeira</a></p>\n<h3>Fontes</h3>\n<ol>\n<li>Tesouro Direto. <a href="https://www.tesourodireto.com.br/conheca/conheca-o-tesouro-direto.htm">Conheça o Tesouro Direto</a>. Consulta em 10/11/2026.</li>\n<li>Fundo Garantidor de Créditos (FGC). <a href="https://www.fgc.org.br/sobre-garantia-fgc">Sobre a garantia FGC</a>. Consulta em 10/11/2026.</li>\n<li>Presidência da República. <a href="https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2004/lei/l11033.htm">Lei nº 11.033, de 21/12/2004 (arts. 1º e 3º)</a>. Consulta em 10/11/2026.</li>\n<li>Banco Central do Brasil. <a href="https://www.bcb.gov.br/publicacoes/comunicadoscopom">Comunicado da 282ª reunião do Copom: Copom mantém a taxa Selic em 13,75% a.a.</a> 04/11/2026.</li>\n<li>Portal do Investidor (CVM). <a href="https://www.gov.br/investidor/pt-br/investir/tipos-de-investimentos/titulos-publicos">Títulos públicos</a>. Consulta em 10/11/2026.</li>\n</ol>',
    'categoria': 'RENDA_FIXA',
    'capa': 'img/artigos/renda-fixa-como-funciona-quem-garante-e-quanto-rende/capa.jpg',
    'capa_alt': 'Mão colocando uma moeda num cofrinho amarelo, ao lado de pilhas de moedas.',
    'capa_credito': 'Foto: Sasun Bughdaryan / Unsplash',
    'com_apoio_ia': True,
    'status': 'RASCUNHO',
}

ANTERIOR = {
    'titulo': 'Renda fixa: como funciona na prática',
    'resumo': 'Entenda o que são títulos de renda fixa e por que costumam ser a porta de entrada dos investidores.',
    'corpo': 'Renda fixa é uma modalidade de investimento em que as regras de remuneração são definidas no momento da aplicação: você "empresta" dinheiro (para o governo, um banco ou uma empresa) e recebe de volta com juros combinados previamente.\n\nÉ considerada uma opção mais previsível que a renda variável, por isso costuma ser o primeiro passo de quem está começando a investir.',
    'categoria': 'RENDA_FIXA',
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
        ('conteudo', '0009_substitui_artigo_renda_variavel_o_que_sao_acoes'),
    ]

    operations = [
        migrations.RunPython(substituir_artigo, desfazer_substituicao),
    ]

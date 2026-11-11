# Gerada por `manage.py exportar_artigo_migracao financas-quantitativas-como-numeros-e-dados-ajudam-a-decidir-onde-investir --substituir o-que-sao-financas-quantitativas`.
# Leva à produção a versão nova de um artigo no lugar da antiga: o artigo
# 'o-que-sao-financas-quantitativas' recebe o conteúdo de 'financas-quantitativas-como-numeros-e-dados-ajudam-a-decidir-onde-investir' e mantém endereço, status e data de
# publicação. Se já estiver publicado, o texto novo vai ao ar com o deploy.
from django.db import migrations

SLUG_ANTIGO = 'o-que-sao-financas-quantitativas'
REVISADO_EM = '2026-11-10'

NOVO = {
    'titulo': 'Finanças quantitativas: como números e dados ajudam a decidir onde investir',
    'slug': 'financas-quantitativas-como-numeros-e-dados-ajudam-a-decidir-onde-investir',
    'resumo': 'Matemática e estatística entraram nos investimentos há mais de 70 anos e já renderam dois prêmios Nobel. Veja a ideia por trás, como ela é usada hoje e onde estão os limites.',
    'corpo': '<aside class="fq-em-30s"><h4>Em 30 segundos</h4><ul>\n<li>Finanças quantitativas usam matemática, estatística e dados para medir retorno e risco e apoiar decisões de investimento.</li>\n<li>A base veio de Harry Markowitz, em 1952: olhar ao mesmo tempo para o retorno esperado e para o quanto ele varia. A ideia rendeu o Nobel de Economia de 1990.</li>\n<li>Hoje, fundos quantitativos transformam padrões dos dados em regras que um programa executa.</li>\n<li>O limite: os modelos aprendem com o passado, e o passado não garante o futuro.</li>\n</ul></aside>\n<aside class="fq-sumario"><h4>Neste artigo</h4><ol>\n<li><a href="#o-que-e">O que são finanças quantitativas?</a></li>\n<li><a href="#de-onde-veio">De onde veio a ideia?</a></li>\n<li><a href="#como-e-usada">Como ela é usada hoje?</a></li>\n<li><a href="#limites">Quais são os limites?</a></li>\n<li><a href="#experimente">Como experimentar no portal?</a></li>\n</ol></aside>\n<p>Finanças quantitativas são a área que usa matemática, estatística e dados para entender como os investimentos se comportam e para apoiar decisões. Em vez de escolher pelo palpite, você mede: quanto um investimento rendeu, quanto oscilou e como ele se move junto com os outros.</p>\n<h2 id="o-que-e">O que são finanças quantitativas?</h2>\n<p>É tratar investimento como um problema de números. As perguntas típicas são: qual é o <strong>retorno esperado</strong> (quanto, em média, se espera ganhar)? Qual é o <strong>risco</strong> (quanto o resultado pode se afastar dessa média)? E como juntar vários investimentos para ter o melhor equilíbrio entre os dois?</p>\n<p>Para responder, usa-se o histórico de preços, balanços de empresas, dados da economia e ferramentas como médias, desvios e correlações.</p>\n<h2 id="de-onde-veio">De onde veio a ideia?</h2>\n<p>Em 1952, o economista Harry Markowitz publicou o ensaio "Portfolio Selection". Ele mostrou que a escolha de uma <strong>carteira</strong> de investimentos pode ser reduzida a equilibrar duas coisas: o retorno esperado e a <strong>variância</strong>, uma medida de quanto os resultados oscilam.</p>\n<p>A segunda grande lição foi a <strong>diversificação</strong>: o risco de uma carteira não depende só do risco de cada investimento isolado, mas de como eles se movem juntos. Por isso, misturar investimentos diferentes reduz o risco. Mas não o elimina, porque na prática os preços costumam andar juntos em parte.</p>\n<blockquote>"O aspecto essencial do risco de um ativo não é o risco de cada ativo isolado, mas a contribuição de cada ativo para o risco da carteira como um todo." (Academia Real Sueca, ao anunciar o Nobel de 1990; tradução livre)</blockquote>\n<p>Markowitz dividiu o Nobel de Economia de 1990 com Merton Miller e William Sharpe. Em 1997, o prêmio foi para Robert Merton e Myron Scholes, que, com Fischer Black (morto em 1995), criaram em 1973 uma fórmula para calcular o preço de <strong>opções</strong>, um tipo de contrato financeiro. Segundo a Academia Real Sueca, milhares de investidores passaram a usá-la todos os dias.</p>\n<aside class="fq-na-pratica"><h4>Na prática</h4>\n<p>Dois investimentos, três anos cada:</p>\n<p>A rendeu 6%, 6% e 6%. Média: 6% ao ano.</p>\n<p>B rendeu 20%, −8% e 6%. Média: (20 − 8 + 6) ÷ 3 = 6% ao ano.</p>\n<p>A média é a mesma, mas B oscila muito mais. O desvio-padrão (a raiz quadrada da variância) de A é zero; o de B é de cerca de 11,4 pontos percentuais. Para Markowitz, B é mais arriscado.</p>\n</aside>\n<h2 id="como-e-usada">Como ela é usada hoje?</h2>\n<p>Os <strong>fundos quantitativos</strong> (ou fundos "quant") são fundos de investimento que automatizam as decisões com base em padrões encontrados nos dados. Segundo o Bora Investir, da B3, o caminho costuma ser este:</p>\n<ul>\n<li>o gestor formula uma hipótese, muitas vezes vinda da pesquisa acadêmica;</li>\n<li>testa a hipótese em dados do passado, como preços, volumes, balanços e indicadores da economia;</li>\n<li>se a hipótese se sustenta, programadores a transformam num sistema que acompanha o mercado e executa as ordens quando o padrão aparece.</li>\n</ul>\n<p>Como qualquer fundo, eles investem nos mesmos ativos que o resto do mercado, podem perder valor e não têm garantia do FGC.</p>\n<h2 id="limites">Quais são os limites?</h2>\n<p>Um modelo é tão bom quanto os dados e as hipóteses por trás dele. O ponto mais importante: os modelos aprendem com o passado, e o futuro pode ser diferente. Um padrão que funcionou por anos pode parar de funcionar quando o cenário muda.</p>\n<p>Outro limite é a própria diversificação: como os investimentos costumam se mover juntos em parte, nenhuma carteira fica livre de risco, por mais variada que seja.</p>\n<h2 id="experimente">Como experimentar no portal?</h2>\n<p>Na Análise de ações do portal, você testa uma regra simples de médias móveis em ações do Ibovespa e compara o resultado com a Selic, com comprar e segurar e com o próprio Ibovespa. Testes estatísticos ajudam a ver se a diferença entre eles é grande o bastante para não ser só acaso.</p>\n<aside class="fq-glossario"><h4>Glossário</h4><dl>\n<dt>Retorno esperado</dt><dd>Quanto, em média, se espera ganhar com um investimento.</dd>\n<dt>Risco</dt><dd>Quanto o resultado pode se afastar do esperado.</dd>\n<dt>Variância</dt><dd>Medida estatística de quanto os resultados oscilam em torno da média.</dd>\n<dt>Desvio-padrão</dt><dd>Raiz quadrada da variância, na mesma unidade dos retornos.</dd>\n<dt>Carteira</dt><dd>Conjunto dos investimentos de uma pessoa ou de um fundo.</dd>\n<dt>Diversificação</dt><dd>Distribuir o dinheiro entre investimentos diferentes para reduzir o risco.</dd>\n<dt>Opção</dt><dd>Contrato que dá o direito, mas não a obrigação, de comprar ou vender um ativo por um preço combinado.</dd>\n<dt>Fundo quantitativo</dt><dd>Fundo que toma decisões com base em modelos matemáticos e estatísticos.</dd>\n</dl></aside>\n<h3>Para saber mais</h3>\n<p><a href="/estudo-caso/">Análise de ações: médias móveis em ações do Ibovespa</a></p>\n<p><a href="/simuladores/juros-compostos/">Simulador de juros compostos</a></p>\n<h3>Fontes</h3>\n<ol>\n<li>The Royal Swedish Academy of Sciences (NobelPrize.org). <a href="https://www.nobelprize.org/prizes/economic-sciences/1990/press-release/">The Prize in Economics 1990: press release</a>. 16/10/1990.</li>\n<li>The Royal Swedish Academy of Sciences (NobelPrize.org). <a href="https://www.nobelprize.org/prizes/economic-sciences/1997/press-release/">The Prize in Economic Sciences 1997: press release</a>. 14/10/1997.</li>\n<li>Harry M. Markowitz. <a href="https://www.nobelprize.org/uploads/2018/06/markowitz-lecture.pdf">Foundations of Portfolio Theory (palestra do Nobel)</a>. 07/12/1990.</li>\n<li>Bora Investir (B3). <a href="https://borainvestir.b3.com.br/tipos-de-investimentos/renda-variavel/fundos-investimento/o-que-sao-fundos-quantitativos/">O que são fundos quantitativos, quais os riscos e como investir?</a> 04/03/2024.</li>\n</ol>',
    'categoria': 'ANALISE_QUANTITATIVA',
    'capa': 'img/artigos/financas-quantitativas-como-numeros-e-dados-ajudam-a-decidir-onde-investir/capa.jpg',
    'capa_alt': 'Tela de notebook com um painel de gráficos de barras e linhas.',
    'capa_credito': 'Foto: Luke Chesser / Unsplash',
    'com_apoio_ia': True,
    'status': 'RASCUNHO',
}

ANTERIOR = {
    'titulo': 'O que são finanças quantitativas?',
    'resumo': 'Um panorama simples sobre como matemática e dados são usados para tomar decisões de investimento.',
    'corpo': 'Finanças quantitativas são a área que usa matemática, estatística e dados para entender o comportamento de investimentos e apoiar decisões financeiras.\n\nEm vez de decidir "no feeling", investidores quantitativos analisam números: histórico de preços, risco, retorno esperado e correlações entre ativos. Neste portal, vamos explicar esses conceitos passo a passo, sem exigir que você já saiba matemática avançada.',
    'categoria': 'FUNDAMENTOS',
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
        ('conteudo', '0007_artigo_revisado_em'),
    ]

    operations = [
        migrations.RunPython(substituir_artigo, desfazer_substituicao),
    ]

"""Título e descrição de cada página para buscadores e prévias de link.

A descrição aparece no Google, e o título e a descrição aparecem na prévia
do link no WhatsApp e nas redes sociais (Open Graph). A chave é o nome da
rota (`namespace:nome`). Rota fora daqui fica com o título e a descrição da
página inicial. A view pode passar `seo_titulo`/`seo_descricao` no contexto
para sobrepor (o detalhe do artigo usa o título e o resumo do próprio artigo).
"""

SITE = 'Portal FinQuant'

PADRAO = (
    'Portal FinQuant — Finanças quantitativas para todos',
    'Portal educativo de finanças quantitativas para quem está começando: artigos em '
    'linguagem simples, simuladores de juros e uma análise de ações com dados reais.',
)

PAGINAS = {
    'core:home': PADRAO,
    'conteudo:lista': (
        'Artigos — Portal FinQuant',
        'Artigos curtos, em linguagem simples, sobre renda fixa, ações e finanças '
        'quantitativas, para quem está começando a investir.',
    ),
    'simuladores:index': (
        'Simuladores — Portal FinQuant',
        'Simuladores gratuitos de juros compostos, dívida no rotativo do cartão e meta '
        'financeira, com o cálculo explicado passo a passo.',
    ),
    'simuladores:juros_compostos': (
        'Simulador de juros compostos — Portal FinQuant',
        'Simule quanto um valor inicial e aportes mensais rendem com juros compostos, '
        'mês a mês, com gráfico e a fórmula explicada.',
    ),
    'simuladores:divida_cartao': (
        'Simulador de dívida no cartão — Portal FinQuant',
        'Veja em quanto tempo a dívida do rotativo do cartão é quitada e quanto você paga '
        'de juros, já com o teto da Lei 14.690/2023.',
    ),
    'simuladores:meta_financeira': (
        'Calculadora de meta financeira — Portal FinQuant',
        'Descubra quanto guardar por mês para chegar a uma meta financeira no prazo que '
        'você escolher, com a evolução mês a mês.',
    ),
    'estudo_caso:index': (
        'Análise de ações — Portal FinQuant',
        'Teste uma regra de médias móveis em ações do Ibovespa e compare o resultado com a '
        'Selic, com comprar e segurar e com o próprio Ibovespa.',
    ),
    'estudo_caso:aviso': (
        'Análise de ações — Portal FinQuant',
        'Teste uma regra de médias móveis em ações do Ibovespa e compare o resultado com a '
        'Selic, com comprar e segurar e com o próprio Ibovespa.',
    ),
    'estudo_caso:analise': (
        'Análise de ações — Portal FinQuant',
        'Teste uma regra de médias móveis em ações do Ibovespa e compare o resultado com a '
        'Selic, com comprar e segurar e com o próprio Ibovespa.',
    ),
    'avaliacoes:avaliar': (
        'Avalie o Portal FinQuant',
        'Conte o que você achou do Portal FinQuant: a sua avaliação ajuda a melhorar o projeto.',
    ),
    'contas:login': ('Entrar — Portal FinQuant', 'Entre na sua conta do Portal FinQuant.'),
    'contas:cadastro': ('Criar conta — Portal FinQuant', 'Crie a sua conta gratuita no Portal FinQuant.'),
}


def titulo_e_descricao(nome_rota):
    return PAGINAS.get(nome_rota, PADRAO)

"""Textos fixos da página, reunidos para facilitar a revisão.

Escritos para quem nunca viu o assunto: termo comum primeiro, técnico entre parênteses.
Textos que dependem do resultado ficam em `quant/leitura.py`. As fontes ficam em `quant/referencias.py`.
"""

TITULO = "Esta regra de compra e venda teria dado certo?"
ABERTURA = ("Você escolhe as ações e uma regra simples. A ferramenta simula o que teria acontecido nos últimos 10 anos "
            "e testa se o resultado merece confiança. Não é preciso saber nada de bolsa: cada passo é explicado.")

# ------------------------------------------------------------------------------- os seis passos
ETAPAS = {
    1: ("Perguntar", "O que queremos saber?"),
    2: ("Preparar", "De onde vêm os dados?"),
    3: ("Processar", "Como os dados foram tratados?"),
    4: ("Analisar", "O que os dados mostram?"),
    5: ("Compartilhar", "Qual é a resposta?"),
    6: ("Agir", "O que fazer com isso?"),
}
SOBRE_ETAPAS = ("Esta página segue os seis passos da análise de dados descritos pelo Google: perguntar, preparar, processar, "
                "analisar, compartilhar e agir. Eles podem se repetir: se algo novo aparecer, dá para voltar a um passo anterior.")
PERGUNTA = ("A pergunta desta análise: uma regra simples de compra e venda rendeu mais que a Selic e que comprar e segurar, "
            "com evidência de que isso não foi acaso?")

# ------------------------------------------------------------------------------- escolhas
ESCOLHA_ACOES = ("Quais ações?", "Escolha de 1 a 10 ações do Ibovespa ou deixe a ferramenta selecionar. Com 2 ou mais, você também escolhe como dividir o dinheiro.")
ESCOLHA_DIVISAO = "Como dividir o dinheiro?"
ESCOLHA_RITMO = ("Qual o ritmo da regra?", "A regra compra quando a média dos preços recentes passa para cima da média dos "
                 "preços mais antigos, e vende no movimento contrário. Os números dizem quantos dias entram em cada média.")
ESCOLHA_PROTECAO = ("Quer uma saída automática?", "Um limite definido na hora da compra: vende se a perda ou o ganho chegar ao percentual escolhido.")
CUSTOS_FIXOS = ("Custos: tarifas da B3 e imposto de renda",
                "A simulação paga os custos reais de quem investe em ações. A <b>tarifa da B3</b> é de 0,03% sobre o valor de cada compra "
                "e de cada venda: numa compra de R$ 10.000, são R$ 3. O <b>imposto de renda</b> incide sobre o lucro: 15% nas operações "
                "comuns, com isenção no mês em que as vendas somam até R$ 20 mil, e 20% no day trade, quando a compra e a venda acontecem "
                "no mesmo dia. A Selic de comparação também paga o imposto da renda fixa, de 22,5% a 15% conforme o prazo. O custo pesa "
                "mais em quem opera muito.")
CUSTO_B3 = ("<b>De onde vem o 0,03%.</b> É a tarifa que a B3, a bolsa brasileira, cobra sobre o valor de cada compra e de cada venda de ações "
            "à vista, fora do day trade, de quem negocia até R$ 3 milhões por dia em média, como a maioria das pessoas físicas. Ela soma três "
            "partes: 0,005% de negociação, 0,0224% de contraparte central (a antiga taxa de liquidação, que garante que a operação se "
            "complete) e 0,0026% de transferência de ativos. Numa compra de R$ 10.000, são R$ 3. Nos leilões de abertura, a parte de "
            "negociação é de 0,007%, e o total vai a 0,032%.")
IMPOSTO = [
    "<b>Operações comuns:</b> 15% sobre o lucro do mês. Fica isento o mês em que as vendas de ações somam até R$ 20 mil. Atenção: "
    "o limite é sobre o valor vendido, não sobre o lucro.",
    "<b>Day trade:</b> quando a compra e a venda acontecem no mesmo pregão, o lucro paga 20%, sem isenção. Nesta simulação, isso só "
    "acontece quando um limite de perda ou de ganho é atingido no próprio dia da compra.",
    "<b>Perdas:</b> o prejuízo de um mês abate o lucro dos meses seguintes, sem prazo, e o de day trade só abate lucro de day trade.",
    "<b>Quando paga:</b> até o último dia útil do mês seguinte, aqui no último pregão desse mês. Na venda com lucro, a regra "
    "separa 15% do lucro (20% no day trade), e esse dinheiro não entra nas compras seguintes. No pagamento, o mês é apurado, "
    "o imposto devido sai da conta e o que sobrou da reserva, por isenção ou por prejuízo, volta para o saldo.",
    "<b>Comprar e segurar</b> paga do mesmo jeito, quando vende: na troca de ações entre janelas e no fim do histórico. Ali, o "
    "imposto sai do patrimônio no pagamento, e a carteira fica menor na mesma proporção dali em diante.",
    "<b>A Selic</b> paga o imposto da renda fixa, retido no resgate: 22,5% até 180 dias, 20% até 360, 17,5% até 720 e 15% depois. A "
    "curva mostra o valor que a pessoa receberia se resgatasse naquele dia. O Ibovespa fica sem imposto, porque é um índice, não um investimento.",
]
IMPOSTO_FORA = ("<b>O que fica de fora:</b> a corretagem, que muitas corretoras zeraram para ações, mas não todas; a diferença entre "
                "o preço de compra e o de venda no livro de ofertas; o imposto retido na fonte (0,005% nas vendas comuns e 1% do lucro "
                "no day trade), que é só uma antecipação descontada do imposto do mês; o mínimo de R$ 10 por guia de pagamento (DARF); "
                "e a taxa de custódia do Tesouro Direto. Para o limite de R$ 20 mil, esta ferramenta soma todas as vendas do mês, "
                "inclusive as de day trade, que é a leitura mais conservadora. As escolhas feitas no treino usam o resultado antes do imposto. "
                "As regras são as vigentes em 07/11/2026: a Medida Provisória nº 1.303/2025, que mudaria as alíquotas, perdeu a validade.")
CAPITAL_FIXO = ("Dinheiro inicial: R$ 100.000",
                "O valor serve apenas para a simulação. Com ele, sempre há dinheiro para comprar quando a regra dá o sinal, e o teste "
                "não fica prejudicado por falta de saldo: a simulação compra lotes inteiros de 100 ações, e com pouco dinheiro uma "
                "ação cara poderia não caber em um lote. Um valor menor não invalida a estratégia. Na bolsa brasileira, dá para "
                "comprar no mercado fracionário, a partir de 1 ação, e o resultado tende a ser proporcionalmente semelhante.")

BOTAO = "Rodar a análise"
VOLTAR = "Voltar ao resultado"
MUDAR = "Mudar escolhas"
CARREGANDO = ("Baixando os preços e testando a regra. Com a seleção automática, são dezenas de ações, "
              "e a primeira vez do dia pode levar cerca de um minuto.")

ALERTA_SELECAO_CURTO = ("<b>Leia o resultado da seleção como uma estimativa otimista.</b> Ela fica com o que foi melhor no treino, sem garantia de que "
                        "se repita no teste. E a lista é a do Ibovespa de hoje: as empresas que afundaram no caminho ficam de fora (viés de "
                        "sobrevivência). A explicação completa está na tela “Como a carteira foi escolhida”.")
ALERTA_SELECAO = ("<b>A seleção escolhe a melhor no treino, não uma vencedora garantida.</b> Antes de cada janela de teste, ela olha só os dados "
                  "anteriores a ela, e a carteira pode perder da Selic no teste."
                  "<br><br><b>A lista é a do Ibovespa de hoje, e isso deixa o resultado melhor do que seria na vida real (viés de sobrevivência).</b> "
                  "A B3 revisa o índice a cada quatro meses e tira as ações que passaram a ser pouco negociadas, que viraram ações de centavos "
                  "ou que deixaram a bolsa por recuperação judicial, falência, fusão ou fechamento de capital. Na maioria dos casos, quem sai "
                  "caiu antes de sair, e quem entrou há pouco costuma ter subido para chegar lá. Com a lista de hoje, a análise volta ao passado "
                  "já sabendo quais empresas deram certo. É usar informação do futuro, que ninguém tinha na época: as que afundaram ficam de fora, e as que "
                  "cresceram participam desde o começo. Por isso, o retorno tende a parecer maior do que um investidor da época teria conseguido."
                  "<br><br><b>Por que essa escolha.</b> Corrigir o viés exigiria a lista do índice em cada data do passado e os preços das empresas "
                  "que saíram da bolsa. O projeto não tem as carteiras antigas do índice, e o Yahoo Finance, fonte gratuita dos preços, deixa de "
                  "ter os dados de quem saiu da bolsa. Por isso, o viés é informado, e não corrigido. Leia o resultado como uma estimativa otimista.")

# ------------------------------------------------------------------------------- uma frase por tela
RESUMO = {
    "preparar": "Os preços vêm do Yahoo Finance, e a Selic, do Banco Central.",
    "processar": "Antes da análise, os dados passam por estes tratamentos.",
    "treino_teste": "O histórico começa com um treino inicial e segue em janelas de teste. Antes de cada janela, as escolhas são refeitas só com os dados anteriores a ela e depois conferidas na janela.",
    "selecao": "A ferramenta testou a regra em cada ação, só no treino, e ficou com as melhores notas.",
    "regra": "A regra compra quando a média curta passa para cima da longa e vende no movimento contrário.",
    "carteira": "Veja como o dinheiro foi dividido e o quanto a estimativa do treino acertou no teste.",
    "dinheiro": "Este é o resultado da regra em reais, depois de pagar as tarifas e o imposto.",
    "sharpe": "O índice de Sharpe responde a uma pergunta: o que a regra rendeu acima da Selic compensou o sobe e desce do caminho?",
    "janelas": "Antes de cada janela de teste, as escolhas foram refeitas só com o passado. Aqui está o que foi escolhido e o que cada janela entregou.",
    "operacoes": "Cada operação é uma compra seguida de uma venda. Aqui está o resumo de todas elas, por período.",
    "sorte": "Estes testes verificam se a diferença encontrada pode ter sido acaso.",
    "variacoes": "Estes testes mudam as condições para ver se o resultado continua de pé.",
    "sequencia": "Estes testes verificam o quanto o resultado depende da ordem e de poucas operações.",
    "compartilhar": "Esta é a resposta à pergunta do início, com o resumo de todos os testes.",
    "agir": "Use o resultado para aprender e comparar. Ele não diz o que comprar.",
}

# ------------------------------------------------------------------------------- explicações
DADOS = ("Um pregão é um dia de negociação na bolsa. Para cada pregão, usamos o preço de abertura, o maior, o menor e o "
         "de fechamento de cada ação. Os preços vêm do Yahoo Finance, já ajustados por dividendos e desdobramentos, "
         "e a Selic vem do Banco Central.")
COLETA = ("Os dados foram coletados em {data}, às {hora} (horário de Brasília). O último pregão usado é o de {ultimo}. "
          "Só entram pregões já encerrados: o dia da coleta fica de fora, para que um preço do meio do pregão não seja lido como fechamento.")
DADO_OU_CALCULO = ("<b>Dado da fonte ou cálculo?</b> Os preços das ações, o Ibovespa e a Selic são dados oficiais, usados como vieram das fontes. "
                   "Todo o resto (retornos, Sharpe, quedas, pesos e testes) é calculado por esta análise a partir deles, e cada cálculo é "
                   "explicado na tela em que aparece.")
ARQUIVOS_USADOS = ("O código de verificação (hash SHA-256) é a impressão digital de cada arquivo: se um único número mudar, o código muda. "
                   "Com ele, dá para conferir que esta análise usou exatamente esses arquivos. Aqui aparecem os 12 primeiros caracteres.")
POR_QUE_10_ANOS = ("Usamos os últimos 10 anos porque um histórico longo passa por fases diferentes: bolsa em alta, bolsa em queda, "
                   "juros altos e juros baixos. Um período curto pode contar só um lado da história.")
DIVISAO_HISTORICO = ("Pense em estudar e fazer uma prova. O treino é o estudo: é onde se pode tentar e escolher. O teste é a prova, com questões que "
                     "não apareceram no estudo. Uma nota alta só no estudo não mostra que a pessoa aprendeu. Por isso, o veredito olha sobretudo para o teste. "
                     "Com janelas, há uma prova por ano: depois de cada uma, o que caiu nela entra no estudo da próxima.")
TT_POR_QUE_JANELAS = ("<b>Por que janelas, e não um corte só.</b> Com um único corte, as escolhas são feitas uma vez e conferidas num só trecho do mercado, "
                      "e o resultado pode depender de onde a linha caiu. Com janelas, cada escolha é refeita com tudo o que já tinha acontecido e conferida "
                      "no período seguinte, em vários momentos diferentes. É a avaliação com origem móvel, descrita por Tashman (2000).")
TT_NAO_INTERCALAR = ("<b>Por que não intercalar treino e teste.</b> Escolher com dados de um ano para testar o ano anterior usaria o futuro, o que ninguém "
                     "tinha na época. E as médias de até 200 pregões atravessariam a divisa entre os blocos, levando informação de um lado para o outro. "
                     "Por isso o treino sempre vem antes do teste.")
TT_JANELAS_LER = [
    "<b>Sharpe:</b> o do treino é o que a escolha prometia, e o da janela é o que ela entregou com dados novos. Se o da janela fica sempre "
    "abaixo, as escolhas não se repetiram.",
    "<b>Retornos:</b> em cada linha, verde com ✓ marca a melhor entre a regra, a Selic e comprar e segurar, e vermelho, a pior.",
    "<b>Leia a sequência:</b> cada janela tem cerca de 1 ano, um período curto. Uma janela isolada diz pouco.",
]

TT_NAO_E_MAQUINA = ("<b>Aqui, treino não é uma máquina aprendendo.</b> A regra de compra e venda é sempre a mesma e não muda com os dados. "
                    "Treino é só o nome do trecho do histórico em que a ferramenta pode fazer escolhas, quando há alguma a fazer.")
TT_TABELA = [
    ["Para que serve", "Fazer as escolhas", "Conferir o resultado"],
    ["O que acontece", "Começa com a primeira metade do histórico e cresce a cada janela", "Cada janela é simulada com escolhas feitas só com os dados anteriores a ela"],
    ["O que olhamos", "O resultado que serviu de base para as escolhas", "Retorno, risco e os testes do veredito, com as janelas em sequência"],
]
TT_SEPARACAO = ("A divisão é feita pela data, antes de qualquer conta. Um teste automático altera os preços da última janela e confirma que nenhuma "
                "escolha anterior a ela muda.")
TT_REGRA = ("Esta é a regra simulada em todo o histórico, com os números da 1ª janela. A forma da regra é a mesma no treino e no teste; "
            "quando o treino escolhe o ritmo, só os dias das médias podem mudar de uma janela para outra.")
DETALHES_SIMULACAO = "Detalhes da simulação: custo, imposto, espera e encerramento"
TT_USOS = [
    "<b>Só o treino inicial:</b> as escolhas da 1ª janela, a correlação e a fronteira eficiente.",
    "<b>O treino que cresce:</b> as escolhas de cada janela seguinte, com todos os pregões anteriores a ela.",
    "<b>Só o teste, com as janelas em sequência:</b> os testes de “Foi sorte?”, de sensibilidade às escolhas e ao custo e os 2 de sequência.",
    "<b>Os dois, comparados:</b> o teste “Foi bem na prova”.",
    "<b>Histórico inteiro:</b> o teste ano a ano.",
]
TT_LIMITES = [
    "<b>O teste só é uma prova independente uma vez.</b> Se você experimentar várias combinações olhando o resultado do teste e ficar com a melhor, ele vira parte do estudo.",
    "<b>Trocar de escolha custa.</b> Quando as escolhas mudam, as posições são vendidas no fim da janela e pagam o custo, como numa troca real de carteira. "
    "Se não mudam, a carteira segue, e uma operação aberta no treino pode continuar na 1ª janela. Na contagem, ela fica no treino, porque as operações são separadas pela data de entrada.",
    "<b>Janelas curtas oscilam.</b> Cada janela tem cerca de 1 ano, e o Sharpe de um ano varia muito. A conclusão vem das janelas em sequência.",
]

TRATAMENTOS = [
    "<b>Preços ajustados.</b> A fonte já desconta dividendos e desdobramentos, para que esses eventos não pareçam ganhos ou perdas. "
    "Por isso, os preços antigos ficam menores que os que se viam na bolsa na época: em fevereiro de 2017, a PETR4 era negociada entre R$ 15 e R$ 16, "
    "e aqui aparece a menos de R$ 4. Os retornos não mudam. Quando a diferença passa de 1%, o quadro de operações mostra também o preço da bolsa.",
    "<b>Datas repetidas.</b> Se uma data aparece mais de uma vez, fica só o último registro.",
    "<b>Dias sem preço.</b> Fechamentos vazios ou não positivos são descartados.",
    "<b>Datas comuns.</b> Com várias ações, entram só as datas em que todas têm preço, sem preencher lacunas.",
    "<b>Histórico mínimo.</b> Ações com menos de {min_pregoes} pregões ficam de fora.",
    "<b>Selic.</b> A taxa diária é acumulada entre um pregão e o seguinte, incluindo os dias sem pregão.",
    "<b>Sinais de erro.</b> A ferramenta procura intervalos de mais de {buraco} dias sem dados, mais de {sem_volume}% dos dias sem negócios "
    "e variações acima de {salto}% em um dia sem movimento do mercado nem volume que as expliquem.",
]
TRATAMENTO_AUTO = ("<b>Na seleção automática.</b> Só entram ações com histórico desde o início do período e sem sinais de erro, "
                   "para que uma ação listada há pouco tempo não encurte a análise de todas.")

REGRA = ("Uma média móvel é a média dos últimos preços de fechamento, recalculada todo dia. Ela suaviza o sobe e desce do preço. "
         "A regra usa duas: uma curta, que reage rápido, e uma longa, que reage devagar. Quando a curta passa para cima da longa, "
         "a regra compra. Quando passa para baixo, vende. Regras desse tipo são estudadas na literatura de finanças, "
         "como em Brock, Lakonishok e LeBaron (1992).")
SEM_TRAPACA_TITULO = "Como a simulação evita trapaças"
SEM_TRAPACA = [
    "<b>Só comprar.</b> A regra só ganha quando a ação sobe. Ela não aposta na queda.",
    "<b>Escolhas só com o passado.</b> Antes de cada janela de teste, ações, pesos e ritmo são escolhidos só com os pregões anteriores a ela.",
]

SELECAO_NOTA = ("<b>Como ler a nota.</b> A nota é o índice de Sharpe no treino. Zero significa render igual à Selic, e maior é melhor. Para entrar, a ação precisa de nota acima de zero "
                "e de ao menos 5 operações no treino, critérios desta ferramenta. Só nessa nota o dinheiro parado rende a Selic, por isso ela não é igual ao Sharpe das outras telas, "
                "em que o dinheiro parado rende zero. O passo a passo está na tela “Treino e teste”.")
SELECAO_COMPARA = ("A comparação com partes iguais de todas as candidatas mostra se selecionar ajudou. "
                   "Se a seleção perde dela, escolher pelo passado não acrescentou valor neste período.")

CARTEIRA = ("Com várias ações, a pergunta é quanto colocar em cada uma. A divisão é calculada antes de cada janela de teste, só com os dados "
            "anteriores a ela, para não usar informação que ninguém teria na época. Nas divisões otimizadas, cada ação fica com no máximo 40%: "
            "pesos estimados com o passado erram, e sem limite a conta tende a pôr quase tudo na ação que mais subiu (DeMiguel, Garlappi e Uppal, 2009).")
CORRELACAO = "Quanto mais baixa a correlação, mais uma ação pode compensar a outra, e é daí que vem o ganho de diversificar."
FRONTEIRA = ("Cada ponto cinza é uma carteira com divisão sorteada: umas espalham o dinheiro entre as ações, outras o concentram em "
             "poucas. A linha é a fronteira eficiente de Markowitz: as divisões com o maior retorno para cada nível de risco, calculadas "
             "no treino inicial, com o mesmo limite por ação da divisão escolhida. A ponta de cima da linha é concentrar o máximo permitido nas ações que mais "
             "renderam no treino. Um ponto abaixo da linha é dominado: existe outro com mais "
             "retorno pelo mesmo risco. Em que lugar da linha ficar depende do quanto cada pessoa aceita oscilar.")
FRONTEIRA_CONCENTRADA = ("<b>Por que “{nome}” fica longe do centro da nuvem.</b> Essa divisão pôs {peso} do dinheiro em {acao}. No treino, "
                         "a carteira oscilou {risco} e rendeu em média {retorno} ao ano. O ponto existe, mas é o mais "
                         "sensível a erro: ele aposta que o passado de uma ação vai se repetir. Num estudo com 14 métodos de otimização "
                         "e 7 bases de dados reais, nenhum superou de forma consistente a divisão em partes iguais fora do período usado "
                         "para calcular os pesos (DeMiguel, Garlappi e Uppal, 2009).")
FRONTEIRA_NOTA = "Atenção: este gráfico avalia comprar e manter as ações, sem a regra de médias. Ele responde só à pergunta de como dividir o dinheiro."
PROMESSA = ("A fronteira usa o passado para estimar o futuro, e essa estimativa erra. Aqui, cada seta sai do que a carteira prometia "
            "no treino inicial e chega ao que entregou nas janelas de teste, com a divisão refeita antes de cada uma. Quanto mais longa a seta, maior o erro.")

DINHEIRO_NAO_E_PASSAR = ("<b>Ganhar dinheiro não é o mesmo que passar nos testes.</b> Este gráfico inclui o treino, em que as escolhas "
                         "foram feitas olhando os próprios dados. O passo 5 explica a diferença.")
DINHEIRO_TITULO = "Entenda melhor: as alternativas e os períodos"
DINHEIRO_ALTERNATIVAS = [
    "<b>Regra:</b> compra e vende pelas médias, com a saída automática escolhida, pagando as tarifas e o imposto.",
    "<b>Comprar e segurar:</b> as mesmas ações e pesos, compradas no primeiro dia e vendidas só quando as escolhas mudam entre "
    "janelas ou no fim. Paga as mesmas tarifas e o mesmo imposto.",
    "<b>Selic:</b> o mesmo dinheiro numa aplicação que rende a taxa básica de juros todo dia. Com imposto, a curva mostra o valor "
    "que a pessoa receberia se resgatasse naquele dia.",
    "<b>Ibovespa:</b> o índice da bolsa, só como retrato do mercado. Não paga tarifa nem imposto, porque não é um investimento.",
]
DINHEIRO_PERIODOS = [
    "<b>Teste (janelas):</b> o trecho em que cada escolha foi conferida com dados que não a influenciaram. É o que conta para o veredito.",
    "<b>Treino inicial:</b> a primeira metade do histórico, onde as primeiras escolhas foram feitas.",
    "<b>Histórico inteiro:</b> os dois juntos, como no gráfico.",
]
AJUSTE_QUADRO = (" Os preços são ajustados por dividendos e desdobramentos posteriores: os antigos ficam menores, e as quantidades, maiores "
                 "que as da época. A linha “na bolsa” mostra o preço que estava na corretora naquele dia. O resultado em R$ e em % não muda.")
QUADRO_OPERACOES = ("<b>Como ler o quadro.</b> Compra e venda trazem a data, a quantidade × o preço e o valor da operação. "
                    "A variação é a do preço, antes de qualquer custo. "
                    "Na linha Total, a variação é a soma em R$ de todas as operações, dividida pelo dinheiro do início. "
                    "As tarifas da B3 somam a compra e a venda. O imposto é apurado por mês, não por operação: aqui, o imposto pago em "
                    "cada mês foi dividido entre as operações com ganho daquele mês, na proporção do ganho de cada uma. Uma operação com "
                    "perda fica com zero, porque ela reduz o imposto do mês ou dos meses seguintes. Por isso, um ganho logo depois de "
                    "perdas pode pagar pouco ou nada. O resultado final é a variação em R$ menos as tarifas e o imposto.")
QUADRO_OPERACOES_SEM_IMPOSTO = ("<b>Como ler o quadro.</b> Compra e venda trazem a data, a quantidade × o preço e o valor da operação. "
                                "A variação é a do preço. "
                                "Na linha Total, a variação é a soma em R$ de todas as operações, dividida pelo dinheiro do início. "
                                "Nesta análise, sem tarifas e sem imposto, o resultado final é a própria variação em R$.")
QUADRO_SALDO = ("<b>Saldo em conta.</b> É o dinheiro parado na conta, somando todas as ações, no fim do pregão da compra e "
                "no da venda. Com uma ação só, cada compra usa todo o saldo, arredondado para baixo em lotes de 100 ações, e a "
                "sobra fica parada. Com várias ações, cada uma recebe a sua parte do dinheiro e opera sozinha; por isso, uma "
                "operação pode abrir enquanto outra, de outra ação, ainda está aberta. A cada janela, o dinheiro é dividido de "
                "novo entre as ações escolhidas. Com imposto, a parte separada para ele na venda com lucro não entra no saldo; "
                "no pagamento, o que sobrou volta. O valor do fim é o dinheiro do início mais o resultado final de todas as "
                "operações, e é igual ao fim da curva do patrimônio.")
DIFICIL_TITULO ="Entenda melhor: por que é tão difícil vencer a Selic e comprar e segurar no Brasil"
DIFICIL_INTRO = ("Não vencer as duas não é defeito desta ferramenta: é o resultado mais comum. A regra começa a corrida com várias "
                 "desvantagens, e elas pesam mais no mercado brasileiro.")
DIFICIL = [
    "<b>A Selic é uma régua alta.</b> Os juros do Brasil estão entre os mais altos do mundo: na última década, a Selic "
    "variou de 2% a 15% ao ano, e passou boa parte do tempo acima de 10%. Ela rende todo dia, sem risco de perder o que já foi ganho. Para valer a pena, "
    "a regra precisa render mais que isso e ainda compensar o risco de cair.",
    "<b>Fora do mercado, o dinheiro da regra fica parado.</b> Enquanto espera o próximo sinal de compra, ele rende zero nesta "
    "simulação, e a Selic continua rendendo. Quanto mais tempo fora, maior a distância.",
    "<b>As médias chegam atrasadas.</b> Elas olham para trás, então a regra compra depois que a alta já começou e vende depois que a "
    "queda já começou. Perde o início das subidas e paga o início das quedas.",
    "<b>Mercado de lado gera sinais falsos.</b> O Ibovespa passa longos períodos subindo e descendo sem direção. Nesses trechos, as "
    "médias se cruzam várias vezes, e a regra compra e vende com prejuízo repetidas vezes.",
    "<b>Cada operação custa, e o imposto chega antes.</b> A regra paga a tarifa da B3 em cada compra e venda e o imposto de renda "
    "no mês em que lucra. Quem compra e segura paga a tarifa poucas vezes e adia o imposto até vender, e o dinheiro que seria "
    "imposto continua rendendo enquanto isso.",
    "<b>Comprar e segurar fica com a alta inteira e com os dividendos.</b> Os preços desta análise incluem os dividendos, que só "
    "entram para quem está com a ação. Muitos dos dias de maior alta vêm logo depois de quedas fortes, justamente quando a regra "
    "costuma estar fora.",
    "<b>Muita gente procura o mesmo padrão.</b> Regras simples de médias são conhecidas há décadas. Quando um padrão fácil de ver dá "
    "lucro, muitos passam a usá-lo, e a vantagem tende a diminuir. Nem gestores profissionais costumam vencer o mercado de forma "
    "consistente depois dos custos (Jensen, 1968).",
]

SHARPE_IDEIA = ("Dois investimentos podem render o mesmo e ter caminhos bem diferentes: um sobe devagar, o outro vive de altos e baixos. "
                "O Sharpe coloca os dois na mesma régua: divide o que cada um rendeu acima da Selic pelo tamanho da oscilação.")
SHARPE_EXEMPLO = ("<b>Exemplo com números ilustrativos.</b> Com a Selic em 12% ao ano, dois investimentos rendem em média 18% ao ano. O primeiro oscila 10% ao ano, e o segundo, 30%. "
                  "Os dois rendem 6 pontos acima da Selic, mas o Sharpe do primeiro é 6 ÷ 10 = 0,60, e o do segundo, 6 ÷ 30 = 0,20. O primeiro entregou o mesmo com menos sobe e desce.")
SHARPE_CONTA_NOTA = ("O retorno médio é a média simples dos retornos diários × 252 pregões. Ele é diferente do “retorno ao ano” da tela “Quanto o dinheiro teria virado”, que é composto. "
                     "A oscilação é o desvio padrão dos retornos diários × √252.")
SHARPE_LEITURA = [
    "<b>Acima de zero:</b> rendeu em média mais que a Selic. O valor diz quantos pontos acima dela vieram para cada ponto de oscilação: 0,50 são 0,5 ponto para cada 1 de oscilação.",
    "<b>Igual a zero:</b> rendeu em média o mesmo que a Selic. Todo o sobe e desce não trouxe nada a mais.",
    "<b>Abaixo de zero:</b> rendeu em média menos que a Selic. O risco não foi pago.",
    "<b>Entre alternativas no mesmo período:</b> maior é melhor. É esse o referencial usado aqui.",
]
SHARPE_LIMITES = [
    "<b>Não há um corte universal.</b> Esta página não usa faixas como “acima de 1 é bom”. Elas circulam no mercado, mas o artigo de Sharpe (1994) não define faixas de bom ou ruim. Por isso, a comparação é com as alternativas no mesmo período.",
    "<b>Depende do período.</b> Sharpe (1994) observa que a medida não é independente do período em que é calculada. Evite comparar valores de períodos diferentes.",
    "<b>O passado não é previsão.</b> Sharpe (1994) considera sujeito a sério questionamento o uso do valor histórico, sem ajustes, como previsão do valor futuro.",
    "<b>Alta e queda pesam igual.</b> A oscilação conta os dois lados, então uma alta forte também aumenta o risco medido. O Sortino, na tela “Quanto o dinheiro teria virado”, olha só o lado de baixo.",
    "<b>Valores negativos pedem cuidado.</b> Com 5 pontos abaixo da Selic, oscilar 10% dá −0,50, e oscilar 20% dá −0,25: mais oscilação parece melhor, só por causa da conta. Entre valores negativos, olhe também o retorno e a queda.",
]

OPERACOES = ("Um cassino perde em muitas rodadas, mas tem uma pequena vantagem matemática que aparece com o tempo. Aqui é igual: "
             "o que importa não é só acertar muito, e sim quanto se ganha quando acerta e quanto se perde quando erra. "
             "Uma regra que acerta pouco pode dar lucro, se os ganhos forem bem maiores que as perdas.")
AVISO_REAIS = ("<b>Como comparar os períodos.</b> Os valores em R$ dependem do dinheiro disponível na época, que cresce ou cai ao longo da simulação. "
               "Entre treino e teste, compare os percentuais, as taxas e os fatores.")
METRICAS_OPERACOES = [
    "<b>Taxa de acerto:</b> operações com ganho ÷ total de operações.",
    "<b>Ganho médio e perda média:</b> a média, em R$, das operações com ganho e das operações com perda, já descontadas as tarifas e antes do imposto.",
    "<b>Ganho médio ÷ perda média (payoff):</b> acima de 1, o ganho típico é maior que a perda típica.",
    "<b>Maior ganho e maior perda:</b> a melhor e a pior operação. Em R$ e em % podem ser operações diferentes, porque o valor em R$ depende do dinheiro aplicado. O percentual é sobre o valor comprado.",
    "<b>Resultado líquido:</b> a soma dos resultados de todas as operações, já descontadas as tarifas e antes do imposto.",
    "<b>Fator de lucro:</b> soma dos ganhos ÷ soma das perdas. Abaixo de 1, a regra perdeu dinheiro.",
    "<b>Resultado médio por operação (expectativa):</b> taxa de acerto × ganho médio − taxa de erro × perda média.",
    "<b>Tarifas pagas:</b> a tarifa da B3 sobre o valor de cada compra e de cada venda. Já estão descontadas do resultado líquido.",
    "<b>Duração média:</b> os pregões de cada operação, contando o da compra e o da venda.",
    "<b>Tempo comprado:</b> a parte dos pregões do período em que a regra estava comprada. Com várias ações, é a média entre elas.",
    "<b>Maior sequência de perdas:</b> o maior número de operações seguidas com perda, em ordem de entrada.",
    "<b>Queda máxima do patrimônio (drawdown):</b> a maior queda do pico ao fundo dentro do período, medida na curva diária. No teste, a curva começa no último fechamento do treino.",
]
METRICAS_DESEMPENHO = [
    "<b>Sharpe:</b> retorno médio acima da Selic ÷ oscilação total, ao ano. A tela “O índice de Sharpe” mostra a conta.",
    "<b>Sortino:</b> como o Sharpe, mas só os dias que renderam menos que a Selic contam como risco, então as altas fortes não pesam contra.",
    "<b>Retorno por queda:</b> retorno ao ano ÷ queda máxima. Mostra quanto rendeu para cada ponto da pior queda. Só faz sentido com queda.",
]

SORTE = ("Jogue uma moeda 10 vezes. Deram 7 caras. A moeda é viciada, ou foi acaso? Os testes fazem a mesma pergunta sobre a regra. "
         "Eles partem da hipótese de que não há diferença nenhuma e calculam a chance de ver um resultado tão extremo assim mesmo.")
P_VALOR = ("Essa chance é o <b>p-valor</b>. Se ele fica abaixo de 0,05, dizemos que há evidência de diferença. O p-valor não é a chance de "
           "a regra funcionar. E um p-valor alto não prova que a regra é ruim: quer dizer que não há evidência suficiente. "
           "Por isso, olhe sempre o tamanho da diferença junto com o p-valor.")
AVISO_PODER = ("Com cerca de {anos} anos de teste, só diferenças grandes costumam aparecer como evidência. Uma vantagem pequena e real "
               "pode passar despercebida.")

VARIACOES = ("Ir bem no estudo não garante ir bem na prova. Um bom resultado também pode "
             "depender de um detalhe ou de um único ano bom. Estes testes mudam as condições para ver se o resultado continua de pé.")

SEQUENCIA = ("Lance um dado várias vezes: os números saem em uma ordem, mas poderiam sair em outra. Com as operações é igual. "
             "A soma final seria a mesma em qualquer ordem, mas o caminho, não. Várias perdas seguidas logo no começo doem muito mais. "
             "Estes testes olham só as operações iniciadas no período de teste.")

LIMITES_TITULO = "O que esta análise não consegue dizer"
LIMITES = [
    "<b>Viés de sobrevivência.</b> A lista de ações é a do Ibovespa de {data}. Empresas que saíram do índice ou quebraram não aparecem, e isso favorece o resultado. "
    "Brown et al. (1992) mostram como amostras só com sobreviventes distorcem estudos de desempenho de fundos.",
    "<b>Viés do período.</b> Os resultados valem para estes 10 anos. Outras fases do mercado podem dar outros resultados.",
    "<b>Amostra pequena.</b> Poucas operações ou poucos anos de teste não permitem concluir muito. Quando isso acontece, a página avisa.",
    "<b>A simulação simplifica.</b> Ela não considera a dificuldade de negociar grandes volumes nem o rendimento do dinheiro parado.",
]
PROXIMOS_PASSOS = ("Experimente outras escolhas e veja o que muda: outro ritmo, outra saída automática, mais ações. Compare os testes, e não só o retorno. "
                   "Se uma combinação só parece boa depois de muitas tentativas, desconfie: é disso que trata o desconto do Sharpe.")

CRITERIOS_INTRO = "Os limites de “passou” usados neste quadro são escolhas técnicas desta ferramenta:"
LIMITE_ACOES = ("<b>Por que no máximo 10 ações.</b> A fronteira de Markowitz não define um número de ações: a conta funciona com quantas "
                "forem escolhidas. Para diversificar, mais ações ajudam. Statman (1987) concluiu que uma carteira de ações sorteadas precisa de "
                "pelo menos 30 a 40 delas, contra a ideia antiga de que 10 bastariam. O limite de 10 vem de outro problema: os pesos são "
                "calculados com estimativas feitas com o passado, e cada ação a mais aumenta o número delas. Com 10 ações, são 65 números "
                "(10 retornos médios e 55 medidas da oscilação de cada ação e de como os pares se movem juntos); com 30, são 495. DeMiguel, Garlappi e Uppal (2009) "
                "calcularam que a divisão otimizada só supera as partes iguais com cerca de 3.000 meses de histórico para 25 ações, e aqui "
                "o treino inicial tem cerca de 60. Por isso o limite de 10 é uma escolha desta ferramenta: ele troca parte da diversificação "
                "por pesos menos sujeitos a erro.")
PARAMETROS = ("Também são escolhas desta ferramenta: 10 anos de histórico, treino inicial de metade do histórico e 5 janelas de teste, "
              "até 10 ações (cada ação a mais aumenta o número de estimativas feitas com o mesmo histórico), no máximo 40% por ação nas divisões otimizadas, os 4 ritmos, as 4 saídas automáticas, "
              "as 10 mil ordens embaralhadas e os lotes de 100 ações. Eles simplificam a análise e não são recomendações.")

# ------------------------------------------------------------------------------- gráficos
GRAFICOS = {
    "regra": ("O preço de uma ação, as duas médias e os pontos em que a regra comprou e vendeu.",
              "Para ver a regra funcionando em um caso real antes de olhar os números."),
    "primeira_operacao": ("O preço da ação, as duas médias, o dia do sinal, a compra e a venda da operação descrita no texto abaixo.",
                          "Para ver no gráfico cada passo da regra: as médias se cruzam, a compra vem na abertura seguinte e a venda fecha a operação."),
    "selecao": ("A nota no treino (Sharpe) de cada ação selecionada, da maior para a menor.",
                "Para mostrar por que estas ações entraram na carteira."),
    "pesos": ("Quanto do dinheiro foi para cada ação.",
              "Para deixar claro como o dinheiro ficou distribuído na simulação."),
    "correlacao": ("O quanto cada par de ações se moveu junto no treino, de −1 a 1.",
                   "Para ver se as ações podem compensar umas às outras."),
    "fronteira": ("Carteiras sorteadas (pontos), a fronteira eficiente (linha) e a posição da carteira escolhida, tudo no treino inicial.",
                  "Para ver se havia divisão com mais retorno pelo mesmo risco."),
    "promessa": ("Setas que saem do que cada carteira prometia no treino e chegam ao que entregou no teste.",
                 "Para medir o quanto o passado errou ao estimar o futuro."),
    "janelas": ("O retorno da regra, da Selic e de comprar e segurar em cada janela de teste.",
                "Para ver se as escolhas funcionaram com dados novos em vários momentos, e não só em um."),
    "curvas": ("O valor do dinheiro ao longo do tempo com a regra e com as referências. A faixa destacada é o teste, e as linhas pontilhadas separam as janelas.",
               "Para responder quanto o dinheiro teria virado e comparar com as alternativas."),
    "hist_operacoes": ("Quantas operações terminaram em cada faixa de resultado, à esquerda ou à direita do empate.",
                       "Para ver se o resultado vem de muitas operações ou de poucas muito grandes."),
    "intervalo": ("A faixa provável do ganho da regra acima da Selic, com o zero marcado.",
                  "Para mostrar o tamanho da incerteza, e não só um número."),
    "ano_a_ano": ("O retorno de cada ano civil, lado a lado com as referências.",
                  "Para ver se o ganho se repete ou depende de poucos anos."),
    "sensibilidade": ("O retorno no teste das combinações de ritmo e saída automática, com a Selic e a sua escolha marcadas.",
                      "Para ver se o resultado depende de um único ajuste."),
    "hist_monte_carlo": ("Quantas ordens simuladas tiveram cada queda máxima, com a queda real e a pessimista marcadas.",
                         "Para ver se a queda real foi típica ou se poderia ter sido pior."),
}

# ------------------------------------------------------------------------------- cada teste
IDEIA = {
    "intervalo": "Em vez de um único número, dá uma faixa plausível para o ganho. Os 95% indicam que, em muitas repetições, faixas calculadas assim conteriam o valor verdadeiro em cerca de 95% das vezes. Se a faixa cruza o zero, ganhar nada a mais é plausível.",
    "alfa": "Separa o que veio de acompanhar a bolsa (beta) do que sobra por mérito da regra (alfa).",
    "desconto": "Quem testa muitas combinações acaba achando uma boa por acaso. O teste desconta isso do resultado.",
    "treino_teste": "Se o resultado cai muito do treino para o teste, ele não se repetiu com dados novos.",
    "ano_a_ano": "Um único ano excelente pode esconder vários ruins. Olhamos cada ano, no histórico inteiro.",
    "sensibilidade": "Roda as 16 combinações de ritmo e saída automática. Se só uma funciona, o resultado pode ser coincidência.",
    "custo": "Roda a mesma simulação com os dois custos, para ver o quanto ele pesa.",
    "monte_carlo": "Refaz as mesmas operações em 10 mil ordens diferentes e mede a maior queda em cada uma.",
    "sem_melhores": "Retira as 3 operações mais lucrativas e refaz a conta.",
}

# Fórmula e ids de `quant/referencias.py`. Lista vazia: a conta é aritmética ou o método é uma escolha desta ferramenta.
CONTA = {
    "intervalo": ("Faixa = média ± 1,96 × (desvio ÷ √n), multiplicada por 252 para ficar ao ano.", []),
    "alfa": ("Regressão com `scipy.stats.linregress`: excesso da regra = alfa + beta × excesso do Ibovespa. Excesso é o que rendeu acima da Selic.",
             ["sharpe1964", "jensen1968"]),
    "desconto": ("t = Sharpe × √anos; p é a chance desse t; p ajustado = 1 − (1 − p)^N, em que N é o número de tentativas; o Sharpe ajustado é o que daria "
                 "esse p em um teste único. A conta supõe tentativas independentes, o caso mais simples.", ["harvey2015", "bailey2014"]),
    "treino_teste": ("Compara o Sharpe do treino inicial com o das janelas de teste em sequência, na mesma curva. Critério desta ferramenta: Sharpe do teste "
                     "positivo e de pelo menos metade do Sharpe do treino inicial.", ["bailey2014", "tashman2000"]),
    "ano_a_ano": ("Retorno composto de cada ano civil. Anos que a análise não cobre inteiros aparecem com o período, como “(até 06/11)”. "
                  "Anos com menos de 126 pregões aparecem no gráfico, mas não entram na contagem.", []),
    "sensibilidade": ("4 ritmos × 4 saídas = 16 simulações do período inteiro, pelas mesmas janelas, com as ações e os pesos escolhidos em cada uma. "
                      "A comparação é com a Selic no teste.", ["bailey2014"]),
    "custo": ("A mesma simulação com as tarifas da B3 (0,03%) e o imposto de renda, e sem nenhum dos dois. A Selic de comparação "
              "também paga ou deixa de pagar o imposto, para as duas ficarem nas mesmas condições.", ["b3_tarifas", "in_rfb_1585", "lei_11033"]),
    "monte_carlo": ("Método desta ferramenta. Cada operação vira um retorno sobre o patrimônio da época. Embaralhamos a ordem 10 mil vezes e medimos a queda máxima, operação a "
                    "operação. O percentil 5% é o cenário pessimista. Por ignorar o sobe e desce dentro de cada operação, essa queda pode ser menor que a do gráfico diário.", []),
    "sem_melhores": ("Soma dos resultados em R$, sem as 3 maiores operações. Critério desta ferramenta: o resultado precisa continuar positivo.", []),
}

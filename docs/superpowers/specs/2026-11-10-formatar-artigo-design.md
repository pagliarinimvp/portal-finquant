# Desenho: nova versão da skill formatar-artigo e da página de artigo

Data: 10/11/2026. Autor do pedido: Marcos Vinicius Pagliarini. Desenho conversado com o Claude.

## Por que

Hoje a skill `formatar-artigo` recebe links prontos e gera um rascunho com estrutura simples (título, lide, intertítulos, fontes). O autor quer duas mudanças:

1. **Começar pelo tema, não pelos links.** O autor sugere um tema; o Claude pesquisa, faz a curadoria das fontes e apresenta a proposta; o autor aprova, corta ou ajusta; só então o artigo é escrito. A qualidade do artigo deixa de depender dos links que o autor traz, e a aprovação vira um ponto de controle claro (bom para o TCC).
2. **Artigo com cara profissional.** Estrutura de portal econômico/guia, completa e organizada, mas com **tom leve e popular**, para um público amplo, **sem abrir mão do rigor técnico**. Com imagem de capa para chamar atenção.

## Metas

- Fluxo tema → pesquisa → curadoria → aprovação → redação → verificação → rascunho.
- Página de artigo com a estrutura combinada (abaixo), incluindo capa.
- Rigor: todo número e toda definição ligados a uma fonte e conferidos antes de criar o rascunho.

## Fora do escopo

- Gerar imagem por IA.
- Mudar as categorias existentes.
- Publicar sozinho: o artigo continua nascendo como rascunho e o autor publica no Admin.

## Antimetas (o que seria falha mesmo funcionando)

- Texto com "economês" ou, no outro extremo, simplificação que deixa o conteúdo errado.
- Número sem fonte, fonte sem data, fonte de baixa confiança (blog de dicas, patrocinado, página sem data).
- Imagem usada sem direito de uso.
- Tom sensacionalista ou de recomendação de investimento.

## Fluxo da skill (decidido pelo autor)

1. **Tema.** O autor sugere um tema (pode vir com links opcionais, que entram na pesquisa como candidatos).
2. **Pesquisa.** O Claude busca na web, priorizando órgãos oficiais (Banco Central, CVM, B3, IBGE, Tesouro Nacional, Receita), completados por imprensa econômica conhecida e estudos acadêmicos.
3. **Proposta de curadoria**, apresentada no chat:
   - **Ângulo:** título provisório, linha fina e as 4 a 5 perguntas que viram as seções.
   - **Fontes escolhidas (4 a 8):** veículo, data, selo de tipo (órgão oficial / imprensa econômica / estudo acadêmico / instituição financeira), o que traz ao artigo e por que é confiável.
   - **Fontes descartadas**, com o motivo (desatualizada, opinativa, paywall, sem data), para o autor poder resgatar.
   - **Imagens:** 1 ou 2 opções de capa de banco gratuito e os gráficos livres encontrados.
   - **Categoria** sugerida (uma das 4 existentes).
4. **Aprovação.** O autor aprova, corta, troca ou pede mais pesquisa. A skill não escreve antes do "aprovado". Ajustes repetem o passo 3.
5. **Redação** na estrutura abaixo.
6. **Verificação** antes de criar o rascunho: cada número e definição conferidos com a fonte (número sem fonte sai do texto); contas do quadro "Na prática" refeitas; revisão ortográfica (acentuação, crase, hífen, concordância); datas em DD/MM/AAAA.
7. **Rascunho** criado pelo `importar_artigo`, como hoje.
8. **Relato ao autor:** slug, URL de prévia, URL do Admin, lista das imagens com crédito e licença.

## Estrutura do artigo (decidida pelo autor: mistura dos modelos B e C)

De cima para baixo:

1. Categoria (selo atual).
2. Título.
3. **Linha fina** (subtítulo de 1–2 frases).
4. **Autoria + data + tempo de leitura.** Autoria: "Por Marcos Vinicius Pagliarini", com nota de transparência "pesquisa e redação com apoio de IA, revisado pelo autor" só nos artigos marcados como feitos com IA (decisão do autor; ver "Nota de IA").
5. **Capa:** foto de banco gratuito, com legenda e crédito.
6. Quadro **"Em 30 segundos"** (3 a 4 pontos-chave).
7. **Sumário** ("Neste artigo") com as perguntas das seções.
8. **Lide** (primeiro parágrafo, já estilizado hoje).
9. **Seções em forma de pergunta** (`h2`), com no máximo 1–2 citações em `blockquote`.
10. Quadro **"Na prática"**: exemplo em reais com a conta passo a passo, conferível na calculadora.
11. **Glossário** dos termos técnicos usados (cada termo também é explicado na primeira aparição).
12. **"Para saber mais"**: link para simulador ou artigo do portal, quando houver um relacionado.
13. **Fontes numeradas e datadas.**

Tom: leve, popular, frases curtas, exemplos do dia a dia; termos técnicos explicados, nunca omitidos; nada de recomendação de investimento.

## Imagens (decidido pelo autor)

- **Capa:** foto de banco gratuito com licença livre (Unsplash, Pexels), sempre com crédito do fotógrafo e do site. É uma **exceção deliberada** à regra de identidade visual "nunca ilustrações decorativas", que vale para os SVGs do site; registrar isso no `CLAUDE.md`.
- **Imagens das fontes:** só entram gráficos/dados de órgãos públicos ou imagens com licença livre, com crédito. Foto ou infográfico de jornal **não** entra na página: vira link nas fontes ("veja o gráfico original") ou o gráfico é refeito com os dados públicos e a fonte indicada.
- Arquivos em `static/img/artigos/<slug>/` (como hoje), versionados no git.

## Mudanças no site necessárias

A estrutura nova não cabe só no `corpo`: capa, linha fina, autoria e tempo de leitura aparecem fora dele e na listagem.

- **Modelo `Artigo`** (migração): campos para a capa (caminho do arquivo estático, texto alternativo, crédito/legenda). Linha fina: reaproveitar `resumo` (já tem até 300 caracteres e já é usado na listagem e na prévia de link). Autoria: texto fixo no template. Nota de IA: condicionada ao campo booleano (ver "Nota de IA").
- **Tempo de leitura:** calculado do `corpo` (contagem de palavras sem HTML), não guardado.
- **`artigo_detail.html`:** linha fina, autoria/nota de IA, data, tempo de leitura e capa acima do corpo.
- **`artigo_list.html`** e cards da página inicial: capa em miniatura quando existir.
- **Prévia de link:** `og:image` do artigo usa a capa quando existir (hoje é sempre `previa.png`).
- **Corpo:** quadros "Em 30 segundos", "Na prática" e glossário precisam de marcação que o sanitizador aceite. Hoje `TAGS_PERMITIDAS` não tem `div`/`aside` nem atributo `class`. O construtor escolhe entre (a) liberar uma tag de quadro com classes restritas a uma lista fixa no `bleach`, ou (b) convenção só com tags já permitidas e estilo por CSS. Escolha do construtor, desde que o sanitizador continue com lista fechada.
- **CSS** (`static/css/site.css`): estilos dos quadros, sumário, glossário, capa e metadados, com os tokens `--fq-*` e variantes do tema escuro.
- **`importar_artigo`:** aceitar os campos novos da capa no JSON e validar que o arquivo da capa existe em `static/`.
- Artigos antigos sem capa continuam funcionando (campos opcionais).

## Restrições

- Sanitizador continua com lista fechada de tags e atributos.
- Idioma pt-BR, datas DD/MM/AAAA no texto visível.
- Identidade "painel institucional" mantida em tudo, exceto a foto de capa.
- A skill vive em `Meus Projetos Claude\Minhas skills\formatar-artigo` (repositório git próprio), ligada ao projeto por junction em `.claude/skills/formatar-artigo`. Editar lá, não no portal.
- A `description` da skill passa para o padrão "Use quando…" em pt-BR, cobrindo os gatilhos novos ("escreve um artigo sobre X", "artigo sobre o tema X").

## Caminho até a produção (decidido pelo autor)

O `.env` local aponta para a branch `dev` do Neon; produção usa a branch `main`. As imagens só chegam à produção com commit e deploy.

- O passo 7 cria o rascunho no banco local (`dev`). A prévia do passo 8 é a local (`python manage.py runserver`, `/artigos/<slug>/` com staff logado).
- Depois de o autor aprovar o rascunho local **e pedir o commit** (regra global: commit só quando o autor pede), a skill gera uma **migração de dados** em `conteudo/migrations/`, no padrão de `0004_importa_artigo_galipolo.py` (commit `2ba2bb4`), que cria o artigo como rascunho em produção no `migrate` do deploy. Texto e imagens chegam no mesmo deploy.
- A migração não deve falhar nem duplicar se o slug já existir no banco (o banco `dev` já terá o artigo quando ela rodar localmente). A reversa remove o artigo pelo slug.
- Nada grava direto no banco de produção.
- O autor publica pelo Admin de produção, como hoje.

## Nota de IA (decidido pelo autor)

- Campo booleano novo no `Artigo` (ex.: `com_apoio_ia`, padrão `False`), editável no Admin.
- A skill marca `True` (o `importar_artigo` aceita o campo no JSON; a migração de dados também o grava).
- Com `True`, a página mostra "Por Marcos Vinicius Pagliarini" + a nota "pesquisa e redação com apoio de IA, revisado pelo autor". Com `False`, só a autoria.
- Artigos existentes ficam com `False`, exceto o do Galípolo, que foi feito pela skill: a migração do campo o marca como `True` (decisão do Claude).

## Deixado para o construtor

- Nomes dos campos, desenho exato do CSS, fórmula do tempo de leitura (ex.: 200 palavras/min).
- Testes: modelo (campos opcionais), tempo de leitura, sanitizador (quadros aceitos, tags fora da lista removidas), `importar_artigo` com e sem capa.

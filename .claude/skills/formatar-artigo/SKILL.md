---
name: formatar-artigo
description: Use when the user gives one or more reference links (news articles, data pages, reports) and wants a publish-ready draft Artigo created for the Portal FinQuant site — e.g. "formata esse link num artigo", "transforma essas notícias em artigo do site".
---

# Formatar artigo

## Visão geral

Transforma um conjunto de links de referência em um rascunho de `Artigo` do
Portal FinQuant, pronto para revisão no Django Admin. Lê cada página, escreve
o artigo no tom "painel institucional" do site (ver `CLAUDE.md`), baixa as
imagens estritamente necessárias e cria o registro via management command —
o artigo nasce como **rascunho** (`status=RASCUNHO`), invisível ao público até
ser revisado e publicado manualmente.

## Fluxo

1. **Coletar links.** Peça um ou mais links ao usuário. Continue perguntando
   "mais algum link?" até ele indicar que terminou.

2. **Definir a categoria.** Escolha uma entre as 4 existentes com base no
   conteúdo lido e confirme com o usuário antes de seguir:
   `FUNDAMENTOS`, `RENDA_FIXA`, `RENDA_VARIAVEL`, `ANALISE_QUANTITATIVA`.

3. **Ler as páginas.** Busque o conteúdo de cada link. Extraia só o que é
   relevante para o artigo — ignore menus, anúncios, comentários.

4. **Selecionar imagens.** Identifique apenas as imagens estritamente
   necessárias ao entendimento do artigo (gráficos, diagramas citados no
   texto). Nunca imagens decorativas, banners ou anúncios. Prefira zero
   imagens a imagens desnecessárias.

5. **Baixar as imagens selecionadas** (se houver) para
   `static/img/artigos/<slug-do-artigo>/`, com nomes descritivos em
   minúsculas e sem espaço (ex. `evolucao-selic.png`). Use `curl` ou
   equivalente via Bash. Gere o `<slug-do-artigo>` com `slugify` do título
   (mesma regra do campo `slug` do modelo — minúsculas, hífens, sem acento).

6. **Compor o artigo** no estilo de matéria de jornal — parágrafo de
   abertura forte, citações de destaque, seções curtas — em vez de blocos
   de texto corrido sem hierarquia:
   - `titulo`: até 200 caracteres.
   - `resumo`: até 300 caracteres, texto curto para a listagem.
   - `corpo`: HTML usando só as tags permitidas pelo sanitizador do site —
     `p`, `br`, `strong`, `em`, `b`, `i`, `h2`, `h3`, `h4`, `a`, `img`,
     `figure`, `figcaption`, `ul`, `ol`, `li`, `blockquote`, `code`, `pre`
     (ver `conteudo/templatetags/conteudo_extras.py`; qualquer outra tag é
     removida na renderização, então não use nada fora dessa lista).
     - **Lead**: o primeiro `<p>` do corpo é estilizado em destaque pelo
       CSS do site — escreva-o como um lide de jornal, resumindo o essencial
       da notícia (o quê, quem, quando) em 1-2 frases, sem enrolação antes
       dele.
     - **Citação de destaque**: quando alguma fonte tiver uma frase forte e
       textual (declaração de uma pessoa, dado marcante), destaque-a com
       `<blockquote>` em vez de deixá-la só dentro de um parágrafo corrido.
       Use com moderação — no máximo 1-2 por artigo, só para frases que
       realmente merecem destaque.
     - Imagens baixadas no passo 5 entram com legenda, dentro de `<figure>`:
       `<figure><img src="/static/img/artigos/<slug>/<nome>.png" alt="...">
       <figcaption>descrição curta da imagem/gráfico e, se aplicável, a
       fonte</figcaption></figure>`.
     - Termine sempre com uma seção de fontes:
       `<h3>Fontes</h3><ul><li><a href="URL-original">título da página</a></li>...</ul>`
       com um item por link lido no passo 1.
   - Tom: neutro, sóbrio, direto, em pt-BR — nada editorial ou sensacionalista
     (ver seção "Identidade visual" do `CLAUDE.md`).

7. **Criar o rascunho.** Grave um arquivo JSON temporário
   (`{"titulo", "resumo", "corpo", "categoria"}`) e rode:
   ```
   python manage.py importar_artigo caminho/para/artigo.json
   ```
   O comando valida tamanhos de campo e categoria, gera um slug único e cria
   o `Artigo` como rascunho. Se ele falhar com erro de validação, corrija o
   campo indicado e rode de novo — não edite o banco diretamente.

8. **Reportar ao usuário:** o slug criado, a URL do artigo no site
   (`/artigos/<slug>/`) — staff logado vê rascunhos nessa mesma URL, com uma
   faixa "Rascunho — não publicado" no topo, então dá pra conferir o
   resultado antes de publicar — a URL do Admin para revisar e publicar
   (impressa pelo próprio comando), e um lembrete de que as imagens baixadas
   vêm de páginas de terceiros — confirme direitos de uso antes de publicar.

## Erros comuns

- **Colocar tag fora da allowlist no `corpo`** (`div`, `span`, `table`,
  atributos `style`) — é removida silenciosamente na renderização. Use só as
  tags listadas no passo 6.
- **Baixar imagem decorativa/de banner** — baixe só o que o texto realmente
  referencia.
- **Esquecer a seção de Fontes** — todo link lido no passo 1 precisa aparecer
  como referência no fim do corpo.
- **Ultrapassar os limites de `titulo` (200) ou `resumo` (300)** — o
  `importar_artigo` rejeita e não cria nada; ajuste o texto e rode de novo.
- **Abusar do `blockquote`** — vira "quadrado" de novo se toda seção tiver
  uma. Reserve para frases realmente marcantes.

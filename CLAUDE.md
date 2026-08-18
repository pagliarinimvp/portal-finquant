# CLAUDE.md

Este arquivo orienta o Claude Code (claude.ai/code) ao trabalhar com código neste repositório.

## Idioma do projeto

O português (pt-BR) é o idioma padrão deste projeto: documentação, comentários no código, mensagens de commit e comunicação com o usuário devem ser em português. Textos técnicos que não têm tradução natural (nomes de bibliotecas, comandos, flags, termos como "MVP" ou "stack") permanecem em inglês onde for o padrão do ecossistema.

## Status

Portal FinQuant — um portal educacional em Django sobre finanças quantitativas para leigos, construído como MVP de TCC. Já está montado com página inicial, artigos, um simulador de juros compostos, cadastro/login de usuário e um formulário de avaliação do site. Veja o `README.md` para instruções de instalação e deploy.

## Comandos

Todos os comandos assumem o ambiente virtual ativado: `source venv/Scripts/activate` (Git Bash) ou `venv\Scripts\activate.bat` (cmd).

- **Rodar o servidor de desenvolvimento:** `python manage.py runserver`
- **Aplicar migrações:** `python manage.py migrate`
- **Criar uma migração após alterar modelos:** `python manage.py makemigrations`
- **Criar um usuário administrador:** `python manage.py createsuperuser`
- **Verificação do sistema (detecta erros de configuração sem subir o servidor):** `python manage.py check`
- **Coletar arquivos estáticos para deploy:** `python manage.py collectstatic --noinput`
- **Shell do Django:** `python manage.py shell`
- Ainda não existe suíte de testes automatizada para o projeto todo (a maioria dos apps tem um `tests.py` vazio, gerado pelo `startapp`); não há test runner configurado além do padrão do Django (`python manage.py test`). O app `simuladores` é a exceção — veja "Padrão dos simuladores" abaixo.

## Arquitetura

Projeto Django monolítico (`config/`) com um app por funcionalidade do MVP, seguindo as convenções padrão do Django (models/views/urls/admin por app, sem camada de API separada — apenas templates renderizados no servidor):

- `core/` — página inicial, busca os 3 artigos mais recentes do app `conteudo`.
- `contas/` — cadastro (`CreateView` + `UserCreationForm`), login/logout (views nativas de `auth` do Django). Usa o modelo padrão `auth.User`, sem customização.
- `conteudo/` — modelo `Artigo` (título, slug, resumo, corpo, categoria) + registro no Django Admin para gestão de conteúdo (sem CMS customizado). Views de listagem e detalhe.
- `simuladores/` — juros compostos, dívida no rotativo do cartão e calculadora de meta financeira, mais uma página-índice em `simuladores:index`. Cálculo puro em `simuladores/views.py`, sem modelo persistido; o resultado é calculado a cada envio do formulário e renderizado na mesma página. Veja "Padrão dos simuladores" abaixo antes de adicionar um novo.
- `avaliacoes/` — modelo `Avaliacao` (nota de 1 a 5 + comentário, com FK opcional para o usuário) que registra o feedback dos usuários sobre o site; esses dados alimentam a análise de qualidade na entrega final do TCC.
- `templates/base.html` — layout compartilhado (navbar, Bootstrap 5 via CDN, mensagens) que os templates de todos os apps estendem.
- `static/css/site.css` — sistema de design do portal (tokens de cor/tipografia, remapeamento das variáveis do Bootstrap). Veja "Identidade visual" abaixo.

As configurações (`config/settings.py`) são lidas de variáveis de ambiente via `django-environ`, a partir de um `.env` local (ignorado pelo git; veja o modelo em `.env.example`). O banco é SQLite, a menos que `DATABASE_URL` esteja definida (produção/Render usa PostgreSQL). Arquivos estáticos são servidos via Whitenoise em produção.

**Planejado, mas ainda não construído (fase 2):** um app `estudo_caso` comparando uma estratégia ativa de compra de ações brasileiras (análise técnica + fundamentalista) com renda fixa e investimento passivo, usando pandas/numpy/yfinance.

## Padrão dos simuladores

Este é o padrão a seguir ao criar um novo simulador em `simuladores/` (estabelecido pelos simuladores de juros compostos, dívida no cartão e meta financeira — use `DividaCartaoView`/`DividaCartaoForm`/`divida_cartao.html` como referência mais completa, por cobrir também o caso de alerta).

- **View**: `FormView` cujo `form_valid` **não redireciona** — chama `self.get_context_data(form=form)`, injeta `contexto['resultado'] = self._calcular(dados)` (um `@staticmethod`) e retorna `self.render_to_response(contexto)`, reexibindo a mesma página com o resultado.
- **Cálculo**: tudo em `Decimal` (nunca `float`, exceto ao converter valores para o gráfico — ver abaixo), iterando mês a mês. Se a simulação puder rodar por muitos meses com o saldo só crescendo (ex.: um cenário de "nunca quita"), envolva o loop com `decimal.localcontext()` e aumente `ctx.prec` (ex.: 60) — o contexto padrão de 28 dígitos estoura em cenários de juros compostos por 600 meses sem nunca diminuir o saldo.
- **Form**: `forms.Form` simples (não `ModelForm` — os simuladores não persistem nada), campos `DecimalField`/`IntegerField` com `widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})`.
- **Rota**: uma entrada em `simuladores/urls.py` (ex.: `path('novo-simulador/', views.NovoSimuladorView.as_view(), name='novo_simulador')`), mais um card novo em `templates/simuladores/index.html` linkando para ela.
- **Template**: estende `base.html`, layout `col-md-5` (formulário) + `col-md-7` (resultado, com placeholder ilustrado quando `resultado` é `None`). O gráfico é um SVG desenhado à mão via JS vanilla (sem Chart.js) — copie o bloco `<style>`+`<script>` de `templates/simuladores/juros_compostos.html` quase 1:1; os dados chegam via `{{ resultado.pontos_grafico|json_script:"pontos-grafico" }}` no formato `[{mes, saldo}, ...]` (saldo em `float`, não `Decimal`, pois é o único ponto onde o JS precisa do valor). Para simuladores de tom de alerta (dívida, por exemplo), troque a paleta do gráfico de `--series-1`/`--series-1-fill` para `var(--fq-rust)`; para simuladores de "crescimento" mantenha a paleta azul padrão.
- **Painel "Como calculamos isso?"**: **obrigatório em todo simulador**, um `<details>` colapsado abaixo da tabela de resultado, com (1) uma frase explicando o método em linguagem simples, (2) a fórmula usada (em `fq-numeros`), e (3) um exemplo numérico pequeno e completo que o usuário consiga conferir manualmente numa calculadora comum. Esse exemplo deve ser reaproveitado como caso de teste unitário de `_calcular` — serve tanto de documentação viva da fórmula quanto de verificação de precisão.
- **Testes**: `simuladores/tests.py` cobre as funções `_calcular` diretamente (`TestCase`, sem precisar de `Client`/request), usando os exemplos do painel "Como calculamos isso?" como valores esperados, mais os casos-limite relevantes (taxa 0%, meta já atingida, dívida que nunca quita etc.).
- **Sem model/admin**: os simuladores são calculadoras stateless — não crie `models.py`/`admin.py` a menos que o simulador precise persistir algo (nenhum precisa até hoje).

## Identidade visual

Direção "painel institucional": neutra, sóbria, funcional — não editorial nem decorativa. Ao criar uma página nova, siga estas convenções em vez de estilizar do zero:

- **Tokens de cor/tipografia**: custom properties com prefixo `--fq-*` no `:root` de `static/css/site.css`, remapeadas nas variáveis nativas do Bootstrap 5.3 (`--bs-primary`, `--bs-body-bg`, `--bs-link-color`, variáveis locais de `.btn-*`/`.table-*`/`.dropdown-menu` etc.) — componentes prontos do Bootstrap herdam a paleta automaticamente, sem precisar de classes extras. Cores principais: `--fq-paper`/`--fq-paper-raised` (fundo/cards), `--fq-ink`/`--fq-ink-muted` (texto), `--fq-teal` (accent slate-azulado — botões, links, destaques), `--fq-gold` (verde-oliva, uso funcional tipo "positivo"), `--fq-rust` (terracota, "negativo"/alerta). Cada uma tem variante redefinida em `[data-bs-theme="dark"]`.
  - **Atenção**: `--fq-ink` e `--fq-paper` invertem de sentido entre os dois temas (ink vira claro no escuro, paper vira escuro). Para algo que precise ficar sempre escuro nos dois temas (ex.: a navbar, o cabeçalho da tabela do simulador), use os tokens fixos `--fq-nav-bg`/`--fq-nav-fg` (ou `--fq-teal`, que também é consistente), nunca `--fq-ink`/`--fq-paper`.
- **Tipografia**: Space Grotesk (títulos, `--fq-font-display`), IBM Plex Sans (corpo, `--fq-font-body`), IBM Plex Mono (números/dados, `--fq-font-mono` — usar a classe `.fq-numeros` em valores monetários/tabelas). Carregadas via Google Fonts no `<head>` do `base.html`.
- **Layout**: cantos quase retos (`--bs-border-radius*` reduzidos), cards sem sombra (só borda 1px em `--fq-rule`), rótulos de seção com a classe `.fq-eyebrow`, divisor de assinatura `.fq-regua` (régua com marcações) abaixo de títulos de seção.
- **Ilustrações**: SVGs de "painel de dados" (gráficos, crachás, medidores — nunca cenas decorativas/ilustrativas) em `templates/ilustracoes/*.svg`, incluídos com `{% include "ilustracoes/nome.svg" %}` (não `<img>`, para herdar `currentColor` e adaptar ao tema). Sempre com `width`/`height` explícitos no `<svg>` (evita ícone gigante antes do CSS carregar) além da classe `fq-ilustracao` (aplica cor e teto de tamanho responsivo).
- **Selos de categoria de artigo**: `templates/conteudo/_categoria_badge.html` — um ícone de linha por categoria; incluir com `{% include "conteudo/_categoria_badge.html" with categoria=artigo.categoria label=artigo.get_categoria_display %}`.
- O `<link>` do `site.css` no `base.html` tem um cache-buster (`?v={% now 'U' %}`) — qualquer edição no CSS aparece sem precisar de hard refresh do navegador.

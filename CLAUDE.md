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
- Ainda não existe suíte de testes automatizados (cada app tem um `tests.py` vazio, gerado pelo `startapp`); não há test runner configurado além do padrão do Django (`python manage.py test`).

## Arquitetura

Projeto Django monolítico (`config/`) com um app por funcionalidade do MVP, seguindo as convenções padrão do Django (models/views/urls/admin por app, sem camada de API separada — apenas templates renderizados no servidor):

- `core/` — página inicial, busca os 3 artigos mais recentes do app `conteudo`.
- `contas/` — cadastro (`CreateView` + `UserCreationForm`), login/logout (views nativas de `auth` do Django). Usa o modelo padrão `auth.User`, sem customização.
- `conteudo/` — modelo `Artigo` (título, slug, resumo, corpo, categoria) + registro no Django Admin para gestão de conteúdo (sem CMS customizado). Views de listagem e detalhe.
- `simuladores/` — calculadora de juros compostos. Cálculo puro em `simuladores/views.py` (`JurosCompostosView._calcular`), sem modelo persistido; o resultado é calculado a cada envio do formulário e renderizado na mesma página.
- `avaliacoes/` — modelo `Avaliacao` (nota de 1 a 5 + comentário, com FK opcional para o usuário) que registra o feedback dos usuários sobre o site; esses dados alimentam a análise de qualidade na entrega final do TCC.
- `templates/base.html` — layout compartilhado (navbar, Bootstrap 5 via CDN, mensagens) que os templates de todos os apps estendem.
- `static/css/site.css` — pequenos ajustes visuais sobre o Bootstrap.

As configurações (`config/settings.py`) são lidas de variáveis de ambiente via `django-environ`, a partir de um `.env` local (ignorado pelo git; veja o modelo em `.env.example`). O banco é SQLite, a menos que `DATABASE_URL` esteja definida (produção/Render usa PostgreSQL). Arquivos estáticos são servidos via Whitenoise em produção.

**Planejado, mas ainda não construído (fase 2):** um app `estudo_caso` comparando uma estratégia ativa de compra de ações brasileiras (análise técnica + fundamentalista) com renda fixa e investimento passivo, usando pandas/numpy/yfinance.

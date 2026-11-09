# Portal FinQuant

Portal web de educação em finanças quantitativas para pessoas leigas, desenvolvido como Trabalho de Conclusão de Curso (TCC). MVP construído com Django.

## Stack

- **Backend/Frontend:** Python 3.12 + Django 6.1 (templates server-side + Bootstrap 5)
- **Banco de dados:** SQLite em desenvolvimento, PostgreSQL em produção
- **Hospedagem sugerida:** Render.com (free tier)

## Funcionalidades do MVP

- Artigos educacionais (`conteudo`), gerenciados pelo Django Admin
- Cadastro e login de usuário, com recuperação de senha por e-mail (`contas`)
- Simulador de juros compostos (`simuladores`)
- Análise de ações (`estudo_caso`, em `/estudo-caso/`): uma regra de compra e venda em ações do Ibovespa, comparada com a Selic, comprar e segurar e o Ibovespa nos últimos 10 anos, com testes estatísticos e resumo em PDF
- Formulário de avaliação do site pelos usuários (`avaliacoes`), com dados exportáveis para análise de qualidade do projeto

## Como rodar localmente

```bash
# 1. Criar e ativar o ambiente virtual (já criado neste repositório em ./venv)
python -m venv venv
source venv/Scripts/activate      # Windows (Git Bash)
# venv\Scripts\activate.bat       # Windows (cmd)

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar variáveis de ambiente
cp .env.example .env
# gere uma SECRET_KEY nova com:
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
# e cole o valor no .env

# 4. Aplicar as migrações (cria o banco SQLite local e popula artigos de exemplo)
python manage.py migrate

# 5. Criar um usuário administrador (para acessar /admin/)
python manage.py createsuperuser

# 6. Criar a tabela onde a análise de ações guarda os resultados
python manage.py createcachetable

# 7. Rodar o servidor de desenvolvimento
python manage.py runserver
```

Análise de ações: os preços ficam em `estudo_caso/dados/` (no git). Para atualizar, `python manage.py atualizar_dados_estudo`. Testes do núcleo do cálculo: `pip install -r requirements-dev.txt` e `pytest estudo_caso/quant_tests`.

Acesse http://127.0.0.1:8000/ no navegador.

## Estrutura do projeto

```
config/         # settings, urls raiz
core/           # home
contas/         # login, cadastro, logout
conteudo/       # artigos educacionais (model, admin, views)
simuladores/    # calculadora de juros compostos
avaliacoes/     # avaliação do site pelos usuários
estudo_caso/    # análise de ações (núcleo quant/, dados/, telas)
templates/      # templates HTML (base.html + por app)
static/         # CSS
```

## Deploy (Render.com)

### Opção rápida: Blueprint

O repositório já tem um `render.yaml`. No dashboard do Render: **New +** →
**Blueprint** → conecte este repositório no GitHub. O Render cria o Web
Service já com `SECRET_KEY` gerada. O banco PostgreSQL fica no
[Neon](https://neon.tech) (o Postgres free do Render é apagado após 30 dias):
crie um projeto no Neon e cole a connection string da branch `main` em
`DATABASE_URL` no formulário do Blueprint. Se for usar login social, preencha
`GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`/`GITHUB_CLIENT_ID`/`GITHUB_CLIENT_SECRET`
no formulário do Blueprint (pode deixar em branco e configurar depois pelo
painel do serviço) — veja o passo a passo das credenciais em
`docs/superpowers/specs/2026-08-17-login-social-design.md`, que também
inclui as URLs de callback de produção a cadastrar no Google e no GitHub
depois que a URL final do serviço existir. Para a recuperação de senha
enviar e-mail de verdade, preencha também `EMAIL_HOST`/`EMAIL_HOST_USER`/
`EMAIL_HOST_PASSWORD`/`DEFAULT_FROM_EMAIL` (com Gmail, veja o `.env.example`). Atenção: o
plano gratuito do Render bloqueia as portas SMTP (25, 465 e 587), então o
envio só funciona num plano pago ou com um serviço de e-mail por API HTTPS.

Para o portal não demorar a abrir depois de um tempo parado (o plano free do
Render desliga o serviço após 15 minutos sem acesso), cadastre um monitor
gratuito (UptimeRobot ou cron-job.org) que acessa `/saude/` a cada 10 minutos.
Essa rota responde "ok" sem consultar o banco, então não mantém o Neon ligado.

### Opção manual

1. Suba o repositório no GitHub.
2. Crie um "Web Service" no Render apontando para o repositório.
3. Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate && python manage.py bootstrap_admin && python manage.py bootstrap_site` (o plano free do Render não suporta pre-deploy command, então migrate e os bootstraps ficam no build mesmo)
   Para a análise de ações, acrescente ao fim: `&& python manage.py createcachetable && python manage.py atualizar_dados_estudo && python manage.py precalcular_estudo`
4. Start command: `gunicorn config.wsgi --workers 1 --threads 4 --timeout 120`
5. Crie um projeto PostgreSQL no Neon e copie a connection string da branch `main` para usar como `DATABASE_URL`.
6. Configure as variáveis de ambiente no painel do Render: `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS` (com o domínio `.onrender.com`), `CSRF_TRUSTED_ORIGINS` (com `https://` + o mesmo domínio), `DATABASE_URL`, `DJANGO_SUPERUSER_USERNAME`/`DJANGO_SUPERUSER_EMAIL`/`DJANGO_SUPERUSER_PASSWORD` (cria o admin no primeiro deploy — veja `contas/management/commands/bootstrap_admin.py`) e, se for usar login social, `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`/`GITHUB_CLIENT_ID`/`GITHUB_CLIENT_SECRET` (veja o passo a passo em `docs/superpowers/specs/2026-08-17-login-social-design.md`, que inclui as URLs de callback de produção a cadastrar no Google e GitHub).

### Atualização semanal dos dados da análise de ações

`.github/workflows/atualizar-dados.yml` dispara um deploy todo sábado à 01:00 de Brasília, e o build baixa os preços novos. Com a variável `ESTUDO_JANELA` (ex.: `2-5`, das 02:00 às 05:00; desligado por padrão até ser validado), o servidor deixa prontas as 60 seleções automáticas e cada ação sozinha com os padrões (`estudo_caso/execucao.py`), cedendo a vez a quem pedir uma análise. Configuração, uma vez só:

1. No Render, serviço `portal-finquant` > Settings > Deploy Hook: copie a URL.
2. No GitHub, Settings > Secrets and variables > Actions > New repository secret, com o nome `RENDER_DEPLOY_HOOK` e a URL como valor.
3. Para testar, rode a rotina à mão em Actions > Atualizar dados da análise de ações > Run workflow.

## Próximos passos (fase 2)

Ver [`PENDENCIAS.md`](PENDENCIAS.md).

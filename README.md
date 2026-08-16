# Portal FinQuant

Portal web de educação em finanças quantitativas para pessoas leigas, desenvolvido como Trabalho de Conclusão de Curso (TCC). MVP construído com Django.

## Stack

- **Backend/Frontend:** Python 3.12 + Django 6.1 (templates server-side + Bootstrap 5)
- **Banco de dados:** SQLite em desenvolvimento, PostgreSQL em produção
- **Hospedagem sugerida:** Render.com (free tier)

## Funcionalidades do MVP

- Artigos educacionais (`conteudo`), gerenciados pelo Django Admin
- Cadastro e login de usuário (`contas`)
- Simulador de juros compostos (`simuladores`)
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

# 6. Rodar o servidor de desenvolvimento
python manage.py runserver
```

Acesse http://127.0.0.1:8000/ no navegador.

## Estrutura do projeto

```
config/         # settings, urls raiz
core/           # home
contas/         # login, cadastro, logout
conteudo/       # artigos educacionais (model, admin, views)
simuladores/    # calculadora de juros compostos
avaliacoes/     # avaliação do site pelos usuários
templates/      # templates HTML (base.html + por app)
static/         # CSS
```

## Deploy (Render.com)

1. Suba o repositório no GitHub.
2. Crie um "Web Service" no Render apontando para o repositório.
3. Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
4. Start command: `gunicorn config.wsgi`
5. Provisione um banco PostgreSQL gerenciado gratuito no Render e copie a `DATABASE_URL` gerada.
6. Configure as variáveis de ambiente no painel do Render: `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS` (com o domínio `.onrender.com`), `CSRF_TRUSTED_ORIGINS` (com `https://` + o mesmo domínio) e `DATABASE_URL`.

## Próximos passos (fase 2)

- App `estudo_caso`: comparação de uma estratégia ativa de compra de ações brasileiras (análise técnica + fundamentalista) com renda fixa e investimento passivo, usando pandas/numpy/yfinance.
- Exportação dos dados de `avaliacoes` (via `pandas`) para a análise de qualidade do projeto na entrega final do TCC.

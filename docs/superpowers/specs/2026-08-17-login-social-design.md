# Login social (Google e GitHub) — Design

Data: 2026-08-17
Status: aprovado para virar plano de implementação

## Contexto e objetivo

Hoje o Portal FinQuant só tem login por usuário/senha (`contas/` — `CreateView` +
`UserCreationForm`, views nativas de `auth` do Django). O objetivo é facilitar o
cadastro/login dos usuários adicionando botões "Entrar com Google" e "Entrar com
GitHub", sem remover o fluxo de usuário/senha existente.

## Decisões já tomadas (das perguntas de brainstorming)

1. Biblioteca: **django-allauth** (padrão de mercado para social auth em Django).
2. Convivência: login social **ao lado** do login/cadastro atual, não substitui.
   `CadastroView` e as views de `auth` do Django continuam como estão.
3. Vinculação de conta: se o e-mail do provedor bate com um usuário local já
   existente, **conecta automaticamente** em vez de erro/duplicata.
4. Escopo de integração: allauth cuida só do handshake OAuth (login/callback).
   As telas próprias (`contas/login.html`, `contas/cadastro.html`) continuam
   sendo as nossas, só ganham botões que apontam pras URLs do allauth.
5. Produção: o projeto ainda não está deployado (Render é só "hospedagem
   sugerida" no README, sem domínio real ainda). O spec cobre só
   `localhost:8000` / `127.0.0.1:8000`; a seção "Deploy" no fim documenta o que
   adicionar quando o domínio de produção existir.

## Arquitetura e componentes

### Dependência nova

- `django-allauth[socialaccount]==65.19.1` — adicionar ao `requirements.txt`
  (versão mais recente no momento deste spec; o extra `[socialaccount]` traz
  as dependências dos provedores OAuth).

### `config/settings.py`

- `INSTALLED_APPS`: adicionar, nesta ordem, `django.contrib.sites`, `allauth`,
  `allauth.account`, `allauth.socialaccount`,
  `allauth.socialaccount.providers.google`,
  `allauth.socialaccount.providers.github`.
- `SITE_ID = 1`.
- `MIDDLEWARE`: adicionar `allauth.account.middleware.AccountMiddleware`
  (obrigatório em versões recentes do allauth).
- `AUTHENTICATION_BACKENDS`: manter o `ModelBackend` padrão (implícito hoje) e
  adicionar `allauth.account.auth_backends.AuthenticationBackend`.
- `LOGIN_REDIRECT_URL` já é `'core:home'` — não muda, allauth respeita essa
  configuração.
- Credenciais dos provedores via `.env` (mesmo padrão do `django-environ` já
  usado no projeto): `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`,
  `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`. Lidas em `SOCIALACCOUNT_PROVIDERS`
  no formato `APPS` (formato atual recomendado pela documentação do allauth,
  evita depender de `SocialApp` cadastrado via Django Admin):

  ```python
  SOCIALACCOUNT_PROVIDERS = {
      "google": {
          "APPS": [{
              "client_id": env("GOOGLE_CLIENT_ID", default=""),
              "secret": env("GOOGLE_CLIENT_SECRET", default=""),
              "key": "",
          }],
          "SCOPE": ["profile", "email"],
      },
      "github": {
          "APPS": [{
              "client_id": env("GITHUB_CLIENT_ID", default=""),
              "secret": env("GITHUB_CLIENT_SECRET", default=""),
              "key": "",
          }],
      },
  }
  ```
- `SOCIALACCOUNT_AUTO_SIGNUP = True` — pula a tela extra de confirmação que o
  allauth mostraria por padrão; login social vira um passo só (clicar no botão
  → autorizar no provedor → volta logado).

### Vinculação automática por e-mail: sem adapter customizado

Pesquisando a documentação atual do allauth (via Context7), descobri que ele já
tem configurações prontas pra exatamente o comportamento que queríamos (item 3
das decisões), sem precisar escrever um adapter próprio:

```python
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
```

- `SOCIALACCOUNT_EMAIL_AUTHENTICATION`: quando um login social traz um e-mail
  verificado que já pertence a um usuário local sem conta social conectada,
  permite logar nessa conta existente em vez de dar erro de e-mail duplicado.
- `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT`: além de permitir o login,
  conecta a conta social à conta local automaticamente (assim, da próxima vez,
  o login funciona mesmo que o e-mail mude no provedor).
- Google e GitHub já reportam e-mail verificado nativamente através do
  provider do allauth (Google via claim `email_verified` do OpenID Connect;
  GitHub via flag `verified` da API `/user/emails`) — não é necessário forçar
  `VERIFIED_EMAIL: True` manualmente pra esses dois provedores.

Nota: usuários locais sem e-mail cadastrado (ex.: o usuário de teste
`teste_9466` criado durante os testes manuais) simplesmente não vinculam com
nada — comportamento esperado, não é um caso a tratar especialmente. Um bom
caso de teste manual real: o usuário `pagliarinimvp` (superusuário) já tem
`pagliarinimvp@gmail.com` cadastrado — logar com Google usando esse mesmo
e-mail deve conectar automaticamente à conta existente, não criar uma nova.

### `config/urls.py`

- Adicionar `path('contas/social/', include('allauth.urls'))`. Usamos só os
  endpoints de OAuth que isso expõe (`.../google/login/`,
  `.../github/login/`, `.../google/login/callback/`,
  `.../github/login/callback/`) — não usamos as telas de conta do allauth.

### Templates

- `templates/contas/login.html` e `templates/contas/cadastro.html`: adicionar,
  abaixo do formulário existente, uma seção com os dois botões, carregando
  `{% load socialaccount %}` e usando `{% provider_login_url 'google' %}` /
  `{% provider_login_url 'github' %}`.
- Cada botão só é renderizado se o provedor correspondente estiver configurado
  (checagem via `{% get_providers %}` do template tag do allauth, que já só
  lista provedores com credenciais válidas) — evita mostrar um botão que vai
  quebrar num setup pela metade (ex.: só Google configurado).
- Estilo: botões Bootstrap `btn-outline-dark w-100`, um ícone inline SVG simples
  de cada provedor (sem adicionar biblioteca de ícones nova) + texto "Entrar
  com Google" / "Entrar com GitHub".

### Banco de dados

- `python manage.py migrate` depois de instalar: allauth cria tabelas próprias
  (`socialaccount_socialaccount`, `socialaccount_socialtoken`,
  `account_emailaddress`, etc.) via suas próprias migrações — nenhuma
  migração nossa precisa ser escrita à mão.

## Fluxo de dados (happy path)

1. Usuário clica em "Entrar com Google" na tela de login ou cadastro.
2. Allauth redireciona pro Google com os escopos padrão (perfil + e-mail).
3. Usuário autoriza no Google.
4. Google redireciona de volta pra
   `/contas/social/google/login/callback/` com um código.
5. Allauth troca o código por token, busca e-mail/perfil.
6. Allauth verifica: já existe usuário local com esse e-mail verificado e
   ainda sem conta social conectada? Com `SOCIALACCOUNT_EMAIL_AUTHENTICATION`
   + `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT` ativados, loga nessa
   conta e conecta a conta social a ela. Não existe? Cria usuário novo, via
   `SOCIALACCOUNT_AUTO_SIGNUP`.
7. Usuário é autenticado e redirecionado pra `core:home` (via
   `LOGIN_REDIRECT_URL`), igual ao fluxo de cadastro atual.

Fluxo do GitHub é idêntico, trocando o provedor.

## Tratamento de erros

- Credencial de um provedor ausente/vazia no `.env` → botão daquele provedor
  não aparece (checado no template, ver acima). Sem erro pro usuário final.
- Provedor não devolve e-mail verificado (raro; GitHub permite e-mail privado,
  mas o allauth já pede o escopo `user:email` por padrão para conseguir o
  e-mail mesmo assim) → não vincula automaticamente; allauth cai no
  comportamento padrão dele (tela de erro "e-mail já em uso" pedindo login
  manual, se o e-mail bater com um usuário existente mas não-verificado; ou
  cria conta nova, se o e-mail não bater com ninguém).
- Usuário cancela a autorização no provedor → allauth redireciona de volta
  pra uma página de erro padrão dele; aceitável para este MVP (sem
  customização extra).

## Testes

**Automatizáveis (parte do plano de implementação):**
- `python manage.py check` sem erros com as novas apps/settings.
- Migração roda limpa.
- Teste de template: botão de um provedor sem credencial configurada não
  aparece no HTML renderizado da página de login; com credencial configurada,
  aparece com o `href` correto.

**Não automatizável (manual, com você, depois das credenciais reais no
`.env`):**
- O handshake OAuth de verdade exige consentimento numa tela real do Google/
  GitHub (às vezes com 2FA) — isso não dá pra dirigir por Playwright/script.
  Depois que as credenciais estiverem no `.env`, testamos juntos:
  1. Clicar no botão, autorizar, confirmar que volta logado.
  2. Conferir em `/admin/auth/user/` e `/admin/socialaccount/socialaccount/`
     que a conta foi criada/conectada corretamente.
  3. Testar o caso de vinculação automática: logar com Google usando
     `pagliarinimvp@gmail.com` (e-mail do superusuário já existente) e
     confirmar que conecta à conta existente em vez de criar uma nova.

## Apêndice: criar as credenciais OAuth

### Google

1. Acesse [Google Cloud Console](https://console.cloud.google.com/) → crie um
   projeto (ou use um existente).
2. **APIs e serviços → Tela de consentimento OAuth**: tipo "Externo", preencha
   nome do app e e-mail de suporte. Pode ficar em modo "Testing" durante o
   desenvolvimento.
3. **APIs e serviços → Credenciais → Criar credenciais → ID do cliente OAuth**:
   tipo "Aplicativo da Web".
4. **URIs de redirecionamento autorizados**: adicione
   `http://127.0.0.1:8000/contas/social/google/login/callback/`.
5. Copie o **Client ID** e o **Client Secret** gerados para
   `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` no `.env`.

### GitHub

1. Acesse **GitHub → Settings → Developer settings → OAuth Apps → New OAuth
   App**.
2. **Homepage URL**: `http://127.0.0.1:8000/`.
3. **Authorization callback URL**:
   `http://127.0.0.1:8000/contas/social/github/login/callback/`.
4. Gere um **Client Secret** na página do app criado.
5. Copie o **Client ID** e o **Client Secret** para `GITHUB_CLIENT_ID` /
   `GITHUB_CLIENT_SECRET` no `.env`.

Ambos os pares de variáveis também entram no `.env.example` (sem valores
reais, só como documentação de que existem).

## Deploy (quando o projeto for hospedado de verdade)

Quando o domínio de produção existir (ex. `portal-finquant.onrender.com`):
- Adicionar a URL de callback de produção em **ambos** os consoles (Google e
  GitHub), além da de desenvolvimento — os dois provedores aceitam múltiplas
  redirect URIs cadastradas no mesmo app.
- Definir `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`/`GITHUB_CLIENT_ID`/
  `GITHUB_CLIENT_SECRET` como variáveis de ambiente no painel do Render, do
  mesmo jeito que `SECRET_KEY` e `DATABASE_URL` já são.
- Sair do modo "Testing" na tela de consentimento OAuth do Google (senão só
  usuários explicitamente adicionados como testadores conseguem logar).

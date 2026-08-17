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

- `django-allauth` — adicionar ao `requirements.txt` (pin de versão exata, sem
  extras de outros provedores).

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
  usado no projeto), lidas em `SOCIALACCOUNT_PROVIDERS`:
  - `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
  - `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`
  - Isso evita depender de `SocialApp` cadastrado via Django Admin — as
    credenciais moram só no `.env`, igual `SECRET_KEY`/`DATABASE_URL`.
- `SOCIALACCOUNT_AUTO_SIGNUP = True` — pula a tela extra de confirmação que o
  allauth mostraria por padrão; login social vira um passo só (clicar no botão
  → autorizar no provedor → volta logado).
- `SOCIALACCOUNT_ADAPTER = 'contas.adapters.SocialAccountAdapter'` — adapter
  próprio (ver seção seguinte).

### `contas/adapters.py` (novo arquivo)

Um `DefaultSocialAccountAdapter` customizado que sobrescreve `pre_social_login`:

- Se já existe um `SocialAccount` para esse login (usuário já conectou antes),
  segue o fluxo padrão do allauth.
- Senão, se o e-mail retornado pelo provedor **é marcado como verificado** pelo
  provedor E bate (case-insensitive) com o `email` de um `User` local
  existente, conecta a `SocialLogin` a esse usuário (`sociallogin.connect`) em
  vez de deixar o allauth tentar criar um usuário novo com e-mail duplicado.
- Caso contrário, comportamento padrão do allauth (cria conta nova, ou mostra
  erro de e-mail já em uso se não for verificado).

Nota: usuários locais sem e-mail cadastrado (ex.: o usuário de teste
`teste_9466` criado durante os testes manuais) simplesmente não vinculam com
nada — comportamento esperado, não é um caso a tratar especialmente.

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
6. `SocialAccountAdapter.pre_social_login` roda: acha usuário local com esse
   e-mail? Conecta. Não acha? Segue fluxo padrão (cria usuário novo, via
   `SOCIALACCOUNT_AUTO_SIGNUP`).
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
- Teste unitário do adapter: simula um `SocialLogin` com e-mail verificado
  batendo um `User` existente → confirma que conecta em vez de tentar criar
  duplicado (e o inverso: e-mail não bate → não conecta).
- Teste de template: botão de um provedor sem credencial configurada não
  aparece no HTML renderizado da página de login.

**Não automatizável (manual, com você, depois das credenciais reais no
`.env`):**
- O handshake OAuth de verdade exige consentimento numa tela real do Google/
  GitHub (às vezes com 2FA) — isso não dá pra dirigir por Playwright/script.
  Depois que as credenciais estiverem no `.env`, testamos juntos: clicar no
  botão, autorizar, confirmar que volta logado e que a conta aparece em
  `/admin/auth/user/`.

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

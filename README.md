# Portal FinQuant

Portal Educacional de Finanças Quantitativas — Trabalho de Conclusão de Curso

---

## Sobre o Projeto

O **Portal FinQuant** é uma aplicação web educacional desenvolvida como TCC, com o objetivo de tornar os conceitos de Finanças Quantitativas acessíveis ao público geral. O portal guia o usuário por uma jornada de aprendizado estruturada, coletando dados de pesquisa no início e avaliando o aprendizado ao final.

## Tecnologias Utilizadas

| Componente | Tecnologia |
|---|---|
| Frontend / Deploy | Streamlit |
| Banco de dados | Supabase (PostgreSQL) |
| Linguagem | Python 3.11+ |
| Visualizações | Plotly |
| Dados de mercado | yfinance (B3) |
| Análise | Pandas, NumPy |

## Estrutura de Arquivos

```
Portal FinQuant/
├── app.py                       # Entry point — navegação e sidebar
├── requirements.txt             # Dependências Python
├── .gitignore
│
├── .streamlit/
│   ├── config.toml             # Tema visual (dark mode)
│   └── secrets.toml            # Credenciais Supabase (NÃO commitar!)
│
├── pages/
│   ├── 1_Apresentacao.py       # Página 1 — Apresentação e Disclaimer
│   ├── 2_Cadastro.py           # Página 2 — Cadastro, Login e Questionário de Perfil
│   ├── 3_Conceitos.py          # Página 3 — Conceitos de Finanças Quantitativas
│   ├── 4_Estudo_de_Caso.py     # Página 4 — Estudo de Caso com dados da B3
│   ├── 5_Avaliacao.py          # Página 5 — Avaliação do Portal
│   └── 6_Agradecimento.py      # Página 6 — Agradecimento
│
├── utils/
│   ├── __init__.py
│   ├── supabase_client.py      # Conexão com o Supabase
│   ├── auth.py                 # Funções de autenticação e persistência
│   └── navigation.py           # Navegação condicional por páginas
│
└── database/
    └── schema.sql              # Script SQL para criar as tabelas no Supabase
```

## Fluxo da Aplicação

```
Página 1 — Apresentação e Disclaimer
    ↓ [Aceitar disclaimer obrigatório]
Página 2 — Cadastro / Login + Questionário de Perfil
    ↓ [Autenticado + Perfil preenchido]
Página 3 — Conceitos de Finanças Quantitativas
    ↓
Página 4 — Estudo de Caso Real (B3)
    ↓
Página 5 — Avaliação do Portal
    ↓ [Avaliação enviada]
Página 6 — Agradecimento
```

> Cada página só fica visível na barra lateral após o usuário cumprir o pré-requisito da etapa anterior.

---

## Configuração e Execução Local

### 1. Clonar o repositório e instalar dependências

```bash
git clone https://github.com/pagliarinimvp/portal-finquant.git
cd portal-finquant
pip install -r requirements.txt
```

### 2. Configurar o Supabase

1. Crie uma conta em [supabase.com](https://supabase.com) e crie um novo projeto
2. Acesse **SQL Editor** no painel do Supabase
3. Copie e execute o conteúdo de `database/schema.sql`
4. Vá em **Settings → API** e copie a **Project URL** e a **anon public key**

### 3. Configurar as credenciais

Edite o arquivo `.streamlit/secrets.toml`:

```toml
[supabase]
url = "https://SEU-PROJETO.supabase.co"
anon_key = "SUA-CHAVE-ANONIMA-AQUI"
```

> ⚠️ **IMPORTANTE:** O arquivo `secrets.toml` já está no `.gitignore`. Nunca o comite!

### 4. Executar localmente

```bash
streamlit run app.py
```

Acesse em: `http://localhost:8501`

---

## Deploy no Streamlit Community Cloud (gratuito)

1. Suba o projeto para um repositório **GitHub público** (sem o `secrets.toml`)
2. Acesse [share.streamlit.io](https://share.streamlit.io) e conecte sua conta GitHub
3. Selecione o repositório e o arquivo `app.py` como entry point
4. Em **Advanced Settings → Secrets**, adicione o conteúdo do `secrets.toml`
5. Clique em **Deploy!**

---

## Configuração do OAuth (Google / GitHub) — Opcional

Para habilitar o login social, configure no painel do Supabase:

1. **Authentication → Providers**
2. Habilite **Google** ou **GitHub**
3. Preencha as credenciais OAuth (client ID e secret) obtidas no Google Cloud Console ou GitHub Settings
4. Configure a URL de callback: `https://SEU-PROJETO.supabase.co/auth/v1/callback`

> Para o protótipo local, o login com e-mail e senha funciona sem configuração adicional.

---

## Análise dos Dados da Pesquisa

Os dados coletados podem ser exportados via:

- **Supabase Dashboard → Table Editor** → selecione a tabela → Export CSV
- **SQL Editor** usando as queries comentadas em `database/schema.sql`

Tabelas disponíveis:
- `usuarios_perfil` — Dados do questionário de perfil (Página 2)
- `avaliacoes` — Avaliações do portal (Página 5)

---

## Personalização da Página 4 (Estudo de Caso)

Para adaptar o estudo de caso ao seu conteúdo específico, edite as variáveis no topo de `pages/4_Estudo_de_Caso.py`:

```python
TITULO_CASO = "Seu título aqui"
SUBTITULO_CASO = "Seu subtítulo aqui"
TICKERS = ["XXXX.SA", "YYYY.SA", ...]  # Tickers da B3
DATA_INICIO = "AAAA-MM-DD"
DATA_FIM = "AAAA-MM-DD"
```

---

*Portal FinQuant © 2025 — Trabalho de Conclusão de Curso — Fins Acadêmicos e Educacionais*

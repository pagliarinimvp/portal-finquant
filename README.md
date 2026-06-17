# 📊 Portal FinQuant

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" />
  <img src="https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white" />
  <img src="https://img.shields.io/badge/Status-Em%20Desenvolvimento-yellow?style=for-the-badge" />
</p>

> **Portal Educacional de Finanças Quantitativas — Trabalho de Conclusão de Curso**

Aplicação web educacional desenvolvida como TCC para democratizar o acesso ao conhecimento em **Finanças Quantitativas**. O portal guia o usuário por uma jornada de aprendizado estruturada em 6 etapas, coletando dados de pesquisa no início e avaliando o aprendizado ao final.

---

## ✨ Funcionalidades

- 🔐 **Autenticação segura** via Supabase (e-mail/senha)
- 📝 **Questionário de perfil** para coleta de dados de pesquisa acadêmica
- 📚 **Conteúdo didático** sobre Finanças Quantitativas com exemplos práticos
- 📊 **Visualizações interativas** com dados reais da B3 (Bolsa do Brasil) via `yfinance`
- 🧪 **Estudo de caso real**: Otimização de Carteira com Simulação de Monte Carlo
- ⭐ **Avaliação do portal** com coleta de feedback acadêmico
- 🔄 **Navegação condicional**: cada etapa só é liberada após o pré-requisito anterior
- 🌙 **Dark mode** com tema customizado

---

## 🛠️ Tecnologias

| Componente | Tecnologia |
|---|---|
| Frontend / Deploy | [Streamlit](https://streamlit.io) |
| Banco de dados | [Supabase](https://supabase.com) (PostgreSQL) |
| Linguagem | Python 3.11+ |
| Visualizações | [Plotly](https://plotly.com) |
| Dados de mercado | [yfinance](https://github.com/ranaroussi/yfinance) (B3) |
| Análise numérica | Pandas, NumPy |

---

## 🗂️ Estrutura de Arquivos

```
portal-finquant/
├── app.py                       # Entry point — navegação e sidebar
├── requirements.txt             # Dependências Python
├── .gitignore
│
├── .streamlit/
│   ├── config.toml             # Tema visual (dark mode)
│   └── secrets.toml            # Credenciais Supabase (❌ NÃO commitar!)
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

---

## 🦭 Fluxo da Aplicação

```
🏠 Página 1 — Apresentação e Disclaimer
        ↓ [Aceitar disclaimer obrigatório]
👤 Página 2 — Cadastro / Login + Questionário de Perfil
        ↓ [Autenticado + Perfil preenchido]
📚 Página 3 — Conceitos de Finanças Quantitativas
        ↓
📈 Página 4 — Estudo de Caso Real (B3)
        ↓
⭐ Página 5 — Avaliação do Portal
        ↓ [Avaliação enviada]
🙏 Página 6 — Agradecimento
```

> 🔐 Cada página só fica visível na barra lateral após o usuário cumprir o pré-requisito da etapa anterior.

---

## 🚀 Configuração e Execução Local

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

Crie o arquivo `.streamlit/secrets.toml` (já está no `.gitignore`):

```toml
[supabase]
url = "https://SEU-PROJETO.supabase.co"
anon_key = "SUA-CHAVE-ANONIMA-AQUI"
```

> ⚠️ **NUNCA commite o arquivo `secrets.toml`!** Ele já está no `.gitignore`.

### 4. Executar localmente

```bash
streamlit run app.py
```

Acesse em: `http://localhost:8501`

---

## ☁️ Deploy no Streamlit Community Cloud

1. Suba o projeto para um repositório **GitHub público** (sem o `secrets.toml`)
2. Acesse [share.streamlit.io](https://share.streamlit.io) e conecte sua conta GitHub
3. Selecione o repositório e o arquivo `app.py` como entry point
4. Em **Advanced Settings → Secrets**, adicione o conteúdo do `secrets.toml`
5. Clique em **Deploy!**

---

## 🗄️ Banco de Dados

O Supabase gerencia duas tabelas principais com **Row Level Security (RLS)** habilitado:

| Tabela | Descrição |
|---|---|
| `usuarios_perfil` | Dados do questionário de perfil (Página 2) |
| `avaliacoes` | Avaliações do portal (Página 5) |

### Exportar dados para análise

- **Supabase Dashboard → Table Editor** → selecione a tabela → Export CSV
- **SQL Editor** usando as queries comentadas em `database/schema.sql`

---

## 🔧 Personalização do Estudo de Caso

Edite as variáveis no topo de `pages/4_Estudo_de_Caso.py`:

```python
TITULO_CASO = "Seu título aqui"
SUBTITULO_CASO = "Seu subtítulo aqui"
TICKERS = ["XXXX.SA", "YYYY.SA", ...]  # Tickers da B3
DATA_INICIO = "AAAA-MM-DD"
DATA_FIM = "AAAA-MM-DD"
```

---

## 🛡️ Segurança

- Credenciais armazenadas em `secrets.toml` (fora do controle de versão)
- Row Level Security habilitado em todas as tabelas do Supabase
- Cada usuário só acessa seus próprios dados
- Passwords gerenciadas pelo Supabase Auth (hash seguro)

---

## ⚠️ Disclaimer

Este portal foi desenvolvido **exclusivamente para fins acadêmicos e educacionais** como parte de um TCC. Nenhuma informação aqui presente constitui recomendação de investimento. Consulte sempre um profissional habilitado antes de tomar decisões financeiras.

---

*Portal FinQuant © 2025 — Trabalho de Conclusão de Curso — Fins Acadêmicos e Educacionais*

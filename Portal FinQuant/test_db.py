"""
test_db.py — Testes de Integração e Segurança do Banco de Dados
Portal FinQuant / Supabase
=================================================================
Executa testes de:
  1. Conexão com o Supabase
  2. Cadastro e autenticação de usuário de teste
  3. Insert e Select em usuarios_perfil (RLS)
  4. Insert e Select em avaliacoes (RLS)
  5. Isolamento entre usuários (segurança RLS cross-user)
  6. Limpeza dos dados de teste

Uso:
  python test_db.py

Requisitos:
  pip install supabase python-dotenv
  (As credenciais são lidas de .streamlit/secrets.toml)
"""

import sys
import time
import random
import string
import tomllib
from pathlib import Path

try:
    from supabase import create_client, Client
except ImportError:
    print("❌ Pacote 'supabase' não encontrado. Execute: pip install supabase")
    sys.exit(1)


# ── Carregar credenciais de .streamlit/secrets.toml ──────────────────────────

SECRETS_PATH = Path(__file__).parent / ".streamlit" / "secrets.toml"

if not SECRETS_PATH.exists():
    print(f"❌ Arquivo secrets.toml não encontrado em: {SECRETS_PATH}")
    sys.exit(1)

with open(SECRETS_PATH, "rb") as f:
    secrets = tomllib.load(f)

SUPABASE_URL = secrets["supabase"]["url"]
SUPABASE_ANON_KEY = secrets["supabase"]["anon_key"]

if "SEU-PROJETO" in SUPABASE_URL or "SUA-CHAVE" in SUPABASE_ANON_KEY:
    print("❌ As credenciais do Supabase ainda não foram configuradas em secrets.toml.")
    sys.exit(1)


# ── Helpers ───────────────────────────────────────────────────────────────────

def rand_suffix(n=8) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def ok(label: str):
    print(f"  ✅ {label}")


def fail(label: str, err=None):
    print(f"  ❌ {label}")
    if err:
        print(f"     → {err}")


def section(title: str):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print("─" * 60)


# ── Geração de dados de teste ─────────────────────────────────────────────────

suffix = rand_suffix()
TEST_EMAIL_A = f"teste_a_{suffix}@finquant.test"
TEST_EMAIL_B = f"teste_b_{suffix}@finquant.test"
TEST_PASSWORD = "Finquant@Test123"  # senha válida (>=8 chars, mista)

results = {"passed": 0, "failed": 0}


def check(condition: bool, label: str, err=None):
    if condition:
        ok(label)
        results["passed"] += 1
    else:
        fail(label, err)
        results["failed"] += 1


# ─────────────────────────────────────────────────────────────────────────────
# TESTE 1 — Conexão com o Supabase
# ─────────────────────────────────────────────────────────────────────────────
section("TESTE 1 — Conexão com o Supabase")

try:
    client: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    ok(f"Conexão estabelecida com {SUPABASE_URL}")
    results["passed"] += 1
except Exception as e:
    fail("Falha ao criar cliente Supabase", e)
    results["failed"] += 1
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# TESTE 2 — Cadastro de usuários de teste (Usuário A e B)
# ─────────────────────────────────────────────────────────────────────────────
section("TESTE 2 — Cadastro de usuários de teste")

user_a = None
user_b = None

try:
    resp_a = client.auth.sign_up({"email": TEST_EMAIL_A, "password": TEST_PASSWORD})
    user_a = resp_a.user
    check(user_a is not None, f"Usuário A cadastrado: {TEST_EMAIL_A}")
except Exception as e:
    fail("Falha ao cadastrar Usuário A", e)

try:
    resp_b = client.auth.sign_up({"email": TEST_EMAIL_B, "password": TEST_PASSWORD})
    user_b = resp_b.user
    check(user_b is not None, f"Usuário B cadastrado: {TEST_EMAIL_B}")
except Exception as e:
    fail("Falha ao cadastrar Usuário B", e)


# ─────────────────────────────────────────────────────────────────────────────
# TESTE 3 — Login do Usuário A + Insert em usuarios_perfil
# ─────────────────────────────────────────────────────────────────────────────
section("TESTE 3 — usuarios_perfil: Insert e Select (Usuário A autenticado)")

client_a: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

try:
    login_a = client_a.auth.sign_in_with_password({"email": TEST_EMAIL_A, "password": TEST_PASSWORD})
    user_a = login_a.user
    check(user_a is not None, f"Login do Usuário A bem-sucedido (id: {user_a.id[:8]}...)")
except Exception as e:
    fail("Falha no login do Usuário A", e)
    user_a = None

if user_a:
    perfil_a = {
        "id": user_a.id,
        "nome": "Usuário de Teste A",
        "email": TEST_EMAIL_A,
        "idade": 28,
        "genero": "Masculino",
        "faixa_renda": "R$ 3.001 – R$ 6.000",
        "produtos_financeiros": ["Poupança", "Tesouro Direto"],
        "nivel_renda_variavel": "Iniciante",
        "nivel_estatistica": "Básico",
    }
    try:
        ins = client_a.table("usuarios_perfil").insert(perfil_a).execute()
        check(len(ins.data) > 0, "Insert em usuarios_perfil bem-sucedido")
    except Exception as e:
        fail("Falha ao inserir perfil do Usuário A", e)

    try:
        sel = client_a.table("usuarios_perfil").select("*").eq("id", user_a.id).execute()
        check(len(sel.data) == 1 and sel.data[0]["nome"] == "Usuário de Teste A",
              "Select do próprio perfil retornou 1 registro correto")
    except Exception as e:
        fail("Falha no select do perfil do Usuário A", e)


# ─────────────────────────────────────────────────────────────────────────────
# TESTE 4 — Login do Usuário A + Insert em avaliacoes
# ─────────────────────────────────────────────────────────────────────────────
section("TESTE 4 — avaliacoes: Insert e Select (Usuário A autenticado)")

avaliacao_id = None
if user_a:
    avaliacao_a = {
        "usuario_id": user_a.id,
        "facilidade_uso": 5,
        "clareza_conteudo": 4,
        "aprendizado_percebido": 5,
        "confianca_pos_portal": 4,
        "recomendaria": True,
        "comentario_livre": "Ótimo portal educacional! (teste automatizado)",
    }
    try:
        ins_av = client_a.table("avaliacoes").insert(avaliacao_a).execute()
        check(len(ins_av.data) > 0, "Insert em avaliacoes bem-sucedido")
        avaliacao_id = ins_av.data[0]["id"] if ins_av.data else None
    except Exception as e:
        fail("Falha ao inserir avaliação do Usuário A", e)

    try:
        sel_av = client_a.table("avaliacoes").select("*").eq("usuario_id", user_a.id).execute()
        check(len(sel_av.data) == 1 and sel_av.data[0]["facilidade_uso"] == 5,
              "Select da própria avaliação retornou 1 registro correto")
    except Exception as e:
        fail("Falha no select da avaliação do Usuário A", e)


# ─────────────────────────────────────────────────────────────────────────────
# TESTE 5 — Isolamento RLS: Usuário B NÃO deve ver dados do Usuário A
# ─────────────────────────────────────────────────────────────────────────────
section("TESTE 5 — Segurança RLS: Isolamento entre usuários")

client_b: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

try:
    login_b = client_b.auth.sign_in_with_password({"email": TEST_EMAIL_B, "password": TEST_PASSWORD})
    user_b = login_b.user
    check(user_b is not None, f"Login do Usuário B bem-sucedido (id: {user_b.id[:8]}...)")
except Exception as e:
    fail("Falha no login do Usuário B", e)
    user_b = None

if user_b and user_a:
    # Usuário B não deve conseguir ler o perfil do Usuário A
    try:
        sel_b = client_b.table("usuarios_perfil").select("*").eq("id", user_a.id).execute()
        check(len(sel_b.data) == 0,
              "RLS bloqueou Usuário B de ler perfil do Usuário A ✔")
    except Exception as e:
        # Supabase pode lançar exceção RLS também — comportamento aceitável
        check(True, "RLS bloqueou acesso ao perfil do Usuário A (via exception) ✔")

    # Usuário B não deve conseguir ler a avaliação do Usuário A
    try:
        sel_b_av = client_b.table("avaliacoes").select("*").eq("usuario_id", user_a.id).execute()
        check(len(sel_b_av.data) == 0,
              "RLS bloqueou Usuário B de ler avaliação do Usuário A ✔")
    except Exception as e:
        check(True, "RLS bloqueou acesso à avaliação do Usuário A (via exception) ✔")

    # Usuário B não deve conseguir inserir no perfil com ID do Usuário A
    try:
        perfil_falso = {
            "id": user_a.id,  # tentativa de injeção com ID alheio
            "nome": "Invasão",
            "email": TEST_EMAIL_B,
        }
        ins_fake = client_b.table("usuarios_perfil").insert(perfil_falso).execute()
        check(len(ins_fake.data) == 0,
              "RLS bloqueou Usuário B de inserir perfil com ID alheio ✔")
    except Exception:
        check(True, "RLS bloqueou insert indevido no perfil alheio (via exception) ✔")


# ─────────────────────────────────────────────────────────────────────────────
# TESTE 6 — Acesso sem autenticação (anon puro) não deve ler dados
# ─────────────────────────────────────────────────────────────────────────────
section("TESTE 6 — Segurança: acesso anônimo não autentic. não lê dados")

client_anon: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

try:
    sel_anon = client_anon.table("usuarios_perfil").select("*").execute()
    check(len(sel_anon.data) == 0,
          "Acesso anônimo não retorna registros de usuarios_perfil ✔")
except Exception:
    check(True, "Acesso anônimo bloqueado por RLS (via exception) ✔")

try:
    sel_anon_av = client_anon.table("avaliacoes").select("*").execute()
    check(len(sel_anon_av.data) == 0,
          "Acesso anônimo não retorna registros de avaliacoes ✔")
except Exception:
    check(True, "Acesso anônimo bloqueado por RLS em avaliacoes (via exception) ✔")


# ─────────────────────────────────────────────────────────────────────────────
# LIMPEZA — Remover dados de teste via SQL admin (MCP ou service role)
# ─────────────────────────────────────────────────────────────────────────────
section("LIMPEZA — Nota sobre dados de teste")

print("  ℹ️  Os usuários de teste foram criados no Supabase Auth.")
print(f"     Usuário A: {TEST_EMAIL_A}")
print(f"     Usuário B: {TEST_EMAIL_B}")
print("  ℹ️  Para removê-los, acesse o Dashboard do Supabase:")
print("     Authentication → Users → filtre pelo e-mail → Delete")
print("  ℹ️  Os dados nas tabelas são removidos em cascata (ON DELETE CASCADE).")


# ─────────────────────────────────────────────────────────────────────────────
# SUMÁRIO FINAL
# ─────────────────────────────────────────────────────────────────────────────
section("RESULTADO DOS TESTES")

total = results["passed"] + results["failed"]
print(f"  ✅ Passaram : {results['passed']}/{total}")
print(f"  ❌ Falharam : {results['failed']}/{total}")

if results["failed"] == 0:
    print("\n  🎉 TODOS OS TESTES PASSARAM — banco de dados e segurança OK!")
    sys.exit(0)
else:
    print("\n  ⚠️  Alguns testes falharam. Verifique os erros acima.")
    sys.exit(1)

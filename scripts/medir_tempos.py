"""Mede o tempo de resposta do Portal FinQuant em produção (Render).

Uso: python scripts/medir_tempos.py resultado.json

Abre cada página 3 vezes (mediana), as telas e o PDF da análise padrão (PETR4), a seleção automática e dois
cálculos novos, medindo a página inicial enquanto eles rodam. As referências da última rodada ficam no
PENDENCIAS.md. Os dois cálculos novos (WEGE3 e a carteira de 4 ações) ficam no cache depois da primeira rodada
na mesma semana de preços: para medir de novo um cálculo sem cache, troque as ações ou as opções.
"""
import re, statistics, sys, threading, time, json
import requests

BASE = "https://portal-finquant.onrender.com"
S = requests.Session()
S.headers["User-Agent"] = "FinQuant-teste-tempo/1.0"
out = {"paginas": [], "analises": [], "durante": []}


def get(path, **kw):
    t = time.perf_counter()
    r = S.get(BASE + path, timeout=180, **kw)
    return r, time.perf_counter() - t


def pagina(nome, path, n=3):
    tempos, cod = [], None
    for _ in range(n):
        r, dt = get(path)
        tempos.append(dt); cod = r.status_code
    item = {"nome": nome, "path": path, "status": cod, "mediana": statistics.median(tempos), "max": max(tempos), "kb": len(r.content) / 1024}
    out["paginas"].append(item)
    print(f"{nome:38s} {cod}  med {item['mediana']:.2f}s  max {item['max']:.2f}s  {item['kb']:.0f} KB", flush=True)
    return r


def analise(nome, query):
    path = "/estudo-caso/analise/?" + query
    t0 = time.perf_counter()
    r, dt = get(path)
    m = re.search(r'data-status-url="([^"]+)"', r.text)
    if not m:
        item = {"nome": nome, "situacao": "cache", "status": r.status_code, "total": dt}
    else:
        status_url, n = m.group(1), 0
        while True:
            time.sleep(1); n += 1
            js = S.get(BASE + status_url, timeout=60).json()
            if js.get("situacao") in ("pronto", "erro"):
                break
            if time.perf_counter() - t0 > 600:
                js = {"situacao": "timeout"}; break
        r2, dt2 = get(path)
        item = {"nome": nome, "situacao": "calculada" if js["situacao"] == "pronto" else js["situacao"],
                "status": r2.status_code, "total": time.perf_counter() - t0, "abrir_pronta": dt2}
    out["analises"].append(item)
    print(f"ANALISE {nome:30s} {item}", flush=True)
    return item


def vigiar(parar):
    while not parar.is_set():
        r, dt = get("/")
        out["durante"].append(dt)
        time.sleep(3)


# 0. acordar
r, dt = get("/saude/"); out["acordar"] = dt
print(f"acordar /saude/ {r.status_code} {dt:.2f}s", flush=True)

# 1. páginas
home = pagina("Início", "/")
pagina("Saúde", "/saude/")
lista = pagina("Artigos (lista)", "/artigos/")
slugs = list(dict.fromkeys(re.findall(r'href="/artigos/([\w-]+)/"', lista.text)))
if slugs:
    pagina("Artigo (detalhe)", f"/artigos/{slugs[0]}/")
pagina("Simuladores (índice)", "/simuladores/")
for s in ("juros-compostos", "divida-cartao", "meta-financeira"):
    pagina(f"Simulador {s}", f"/simuladores/{s}/")
# POST do simulador de juros compostos (com CSRF)
r, _ = get("/simuladores/juros-compostos/")
tok = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.text).group(1)
tp = []
for _ in range(3):
    t = time.perf_counter()
    rp = S.post(BASE + "/simuladores/juros-compostos/", data={"csrfmiddlewaretoken": tok, "valor_inicial": "1000", "aporte_mensal": "100",
               "taxa_mensal": "1", "periodo_taxa": "mensal", "meses": "120"}, headers={"Referer": BASE + "/simuladores/juros-compostos/"}, timeout=60)
    tp.append(time.perf_counter() - t)
out["paginas"].append({"nome": "Juros compostos (calcular, POST)", "path": "POST", "status": rp.status_code, "mediana": statistics.median(tp), "max": max(tp), "kb": len(rp.content) / 1024})
print(f"POST juros compostos {rp.status_code} med {statistics.median(tp):.2f}s", flush=True)
for nome, p in (("Entrar", "/contas/entrar/"), ("Cadastro", "/contas/cadastro/"), ("Esqueci a senha", "/contas/esqueci-a-senha/"),
                ("Avaliação", "/avaliacao/"), ("Análise de ações (passo 1)", "/estudo-caso/")):
    pagina(nome, p)

# 2. análise de ações já pronta (padrão PETR4): todas as telas + PDF
q = "selecao=manual&tickers=PETR4&medias=intermediario&protecao=2_1&divisao=igual"
analise("Padrão PETR4 (pré-calculada)", q)
r = pagina("Análise PETR4 tela 0", f"/estudo-caso/analise/?{q}&tela=0")
n = max([int(x) for x in re.findall(r"tela=(\d+)", r.text)] + [0])
for i in range(1, n + 1):
    pagina(f"Análise PETR4 tela {i}", f"/estudo-caso/analise/?{q}&tela={i}", n=2)
pagina("Análise PETR4 resumo PDF", f"/estudo-caso/pdf/?{q}", n=2)

# 3. automática (deve estar no cache do pré-cálculo)
analise("Seleção automática (padrão)", "selecao=automatica&medias=intermediario&protecao=2_1&divisao=igual")

# 4. cálculos novos, com o vigia medindo a página inicial ao mesmo tempo
parar = threading.Event(); th = threading.Thread(target=vigiar, args=(parar,)); th.start()
analise("1 ação nova (WEGE3)", "selecao=manual&tickers=WEGE3&medias=rapido&protecao=1_1&divisao=igual")
analise("4 ações novas", "selecao=manual&tickers=ITUB4&tickers=BBDC4&tickers=ABEV3&tickers=WEGE3&medias=lento&protecao=3_1&divisao=min_variancia")
parar.set(); th.join()
d = out["durante"]
print(f"Início durante cálculo: n={len(d)} med {statistics.median(d):.2f}s max {max(d):.2f}s", flush=True)

json.dump(out, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)

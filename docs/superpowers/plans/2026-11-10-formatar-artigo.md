# Nova skill formatar-artigo e página de artigo profissional — Plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A skill passa a partir de um tema (pesquisa → curadoria → aprovação → redação → verificação), e a página de artigo ganha capa, linha fina, autoria com nota de IA, tempo de leitura e quadros, com o rascunho chegando à produção por migração de dados.

**Architecture:** Campos novos opcionais no `Artigo` (capa, texto alternativo, crédito, `com_apoio_ia`). O sanitizador do corpo passa a aceitar um `aside` com classes de uma lista fechada, `dl/dt/dd` e `id` em `h2`. Templates e CSS mostram a estrutura nova. Dois comandos: `importar_artigo` (já existe, ganha campos e validação da capa) e `exportar_artigo_migracao` (novo, gera a migração de dados para produção). A skill é reescrita no repositório próprio dela.

**Tech Stack:** Django 6.1, bleach 6.2, Pillow 13 (já instalado como dependência do reportlab), Bootstrap 5.3, `TestCase` do Django.

**Spec:** `docs/superpowers/specs/2026-11-10-formatar-artigo-design.md`

## Global Constraints

- **Sem commit nem push sem o autor pedir** (regra global do autor). Os passos "Conferir diff" substituem os commits; ao fim, lembrar o autor do que não foi enviado.
- Testes do portal: `source venv/Scripts/activate && python manage.py test conteudo` (rodam no SQLite, mesmo com `DATABASE_URL` definida).
- Todo texto visível em pt-BR, revisado (acentuação, crase, hífen, concordância). Datas visíveis em DD/MM/AAAA.
- Arquivos editados por script Python: `write_text(..., newline="")` ou `write_bytes`. Conferir `git diff --numstat` (nenhum arquivo inteiro reescrito por troca de fim de linha).
- Sanitizador continua com lista fechada de tags, atributos e classes.
- Cores só por tokens `--fq-*`, com variante no tema escuro quando o token não se ajusta sozinho.
- Textos fixos (copiar exatamente): autoria `Por Marcos Vinicius Pagliarini`; nota de IA `Pesquisa e redação com apoio de IA, revisado pelo autor.`
- Capa: arquivo em `static/img/artigos/<slug>/capa.jpg` (ou `.png`/`.webp`), **1200×630 px**, mesmo formato da prévia de link (`base.html` declara `og:image:width=1200`, `height=630`).
- A skill vive em `C:\Users\pagli\Desktop\Meus Projetos Claude\Minhas skills\formatar-artigo\SKILL.md` (repositório git próprio), ligada ao projeto por junction. Editar lá.

## Review Focus

1. **Artigo antigo, sem capa:** página, lista, página inicial e prévia de link funcionam como hoje (prévia volta para `previa.png`). → teste na Task 3.
2. **Capa cadastrada mas ausente do manifesto em produção** (deploy sem a imagem, ou caminho digitado errado no Admin): `{% static %}` com `CompressedManifestStaticFilesStorage` levanta `ValueError` e daria erro 500. A página deve abrir sem a capa. → filtro `capa_url` na Task 2, teste com storage de manifesto simulado.
3. **Links do sumário (`href="#…"`)** não podem abrir em nova aba nem ganhar `nofollow` como os links externos. → teste na Task 2.
4. **Corpo com aspas, apóstrofos, acentos, quebras de linha e `\`** precisa sair idêntico do banco local para a migração exportada. → teste de ida e volta na Task 5.
5. **Migração exportada rodando onde o slug já existe** (banco `dev`, que já tem o rascunho): não duplica nem falha; a reversa apaga só esse slug. → teste na Task 5.

---

### Task 1: Campos novos no modelo `Artigo`

**Files:**
- Modify: `conteudo/models.py`
- Create: `conteudo/migrations/0006_artigo_capa_e_apoio_ia.py` (gerada com `makemigrations`, depois acrescida de `RunPython`)
- Modify: `conteudo/admin.py`
- Test: `conteudo/tests.py`

**Interfaces:**
- Produces: `Artigo.capa: CharField(max_length=200, blank=True)` — caminho relativo a `static/`, ex. `img/artigos/<slug>/capa.jpg`; `Artigo.capa_alt: CharField(max_length=200, blank=True)`; `Artigo.capa_credito: CharField(max_length=300, blank=True)` — ex. `Foto: Fulano / Unsplash`; `Artigo.com_apoio_ia: BooleanField(default=False)`. Todos com `help_text` em pt-BR.

- [ ] **Step 1: Escrever os testes que falham** (classe `CamposNovosTests`)

```python
def test_artigo_sem_capa_e_sem_ia_por_padrao(self):
    a = criar_artigo('sem-capa')
    self.assertEqual(a.capa, '')
    self.assertFalse(a.com_apoio_ia)

def test_migracao_marca_o_artigo_do_galipolo_como_feito_com_ia(self):
    # A 0004 cria o rascunho; a 0006 o marca.
    galipolo = Artigo.objects.get(slug='galipolo-defende-juros-restritivos-para-reequilibrar-oferta-e-demanda-no-brasil')
    self.assertTrue(galipolo.com_apoio_ia)
    self.assertFalse(Artigo.objects.exclude(pk=galipolo.pk).filter(com_apoio_ia=True).exists())
```

- [ ] **Step 2:** `python manage.py test conteudo.tests.CamposNovosTests` → FAIL (`AttributeError`/campo inexistente).
- [ ] **Step 3:** Acrescentar os 4 campos ao modelo; `python manage.py makemigrations conteudo --name artigo_capa_e_apoio_ia`; na migração gerada, acrescentar `RunPython(marcar_galipolo, desmarcar_galipolo)` depois dos `AddField`, filtrando pelo slug acima.
- [ ] **Step 4:** No `ArtigoAdmin`, acrescentar `com_apoio_ia` a `list_display` e `list_filter`, e `fieldsets` com um grupo "Capa" (`capa`, `capa_alt`, `capa_credito`) e `com_apoio_ia` junto de `status`.
- [ ] **Step 5:** `python manage.py test conteudo` → PASS (todos, inclusive os antigos).
- [ ] **Step 6: Conferir diff** — `git diff --numstat`.

---

### Task 2: Sanitizador, tempo de leitura e URL segura da capa

**Files:**
- Modify: `conteudo/templatetags/conteudo_extras.py`
- Test: `conteudo/tests.py`

**Interfaces:**
- Produces:
  - `CLASSES_DE_QUADRO = {'fq-em-30s', 'fq-sumario', 'fq-na-pratica', 'fq-glossario'}`
  - filtro `corpo_seguro` passa a aceitar `aside` (só atributo `class`, só um valor de `CLASSES_DE_QUADRO`), `dl`, `dt`, `dd`, e `id` em `h2` casando `^[a-z0-9-]{1,80}$`.
  - filtro `tempo_leitura(corpo: str) -> int` — minutos, `ceil(palavras / 200)`, mínimo 1, palavras contadas sem HTML (`strip_tags`).
  - filtro `capa_url(caminho: str) -> str` — `static(caminho)`; devolve `''` se `caminho` vazio ou se `static()` levantar `ValueError`.

- [ ] **Step 1: Escrever os testes que falham** (em `CorpoSeguroTests` e nova `FiltrosArtigoTests`)

```python
def test_aceita_quadro_com_classe_da_lista(self):
    html = corpo_seguro('<aside class="fq-na-pratica"><p>x</p></aside>')
    self.assertIn('<aside class="fq-na-pratica">', html)

def test_remove_classe_fora_da_lista(self):
    html = corpo_seguro('<aside class="btn btn-danger"><p>x</p></aside>')
    self.assertNotIn('btn', html)

def test_classe_nao_vale_em_outras_tags(self):
    self.assertNotIn('class', corpo_seguro('<p class="fq-na-pratica">x</p>'))

def test_aceita_glossario_em_dl(self):
    html = corpo_seguro('<dl><dt>Copom</dt><dd>Comitê.</dd></dl>')
    self.assertIn('<dt>Copom</dt>', html)

def test_aceita_id_simples_em_h2(self):
    self.assertIn('id="o-que-e"', corpo_seguro('<h2 id="o-que-e">O que é?</h2>'))

def test_remove_id_com_caracteres_estranhos(self):
    self.assertNotIn('id=', corpo_seguro('<h2 id="x\" onclick=\"y">T</h2>'))

def test_link_do_sumario_nao_abre_em_nova_aba(self):
    html = corpo_seguro('<a href="#o-que-e">O que é?</a>')
    self.assertNotIn('target', html)
    self.assertNotIn('nofollow', html)

def test_link_externo_continua_em_nova_aba(self):  # regressão
    self.assertIn('target="_blank"', corpo_seguro('<a href="https://bcb.gov.br">BC</a>'))

def test_tempo_leitura(self):
    self.assertEqual(tempo_leitura('<p>' + 'palavra ' * 401 + '</p>'), 3)
    self.assertEqual(tempo_leitura(''), 1)

def test_capa_url_vazia(self):
    self.assertEqual(capa_url(''), '')

@override_settings(STORAGES={**settings.STORAGES, 'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'}})
def test_capa_url_ausente_do_manifesto_nao_quebra(self):
    self.assertEqual(capa_url('img/artigos/nao-existe/capa.jpg'), '')
```

(Se o `ManifestStaticFilesStorage` sem manifesto não levantar `ValueError` no ambiente de teste, simular com `mock.patch('conteudo.templatetags.conteudo_extras.static', side_effect=ValueError)`.)

- [ ] **Step 2:** `python manage.py test conteudo` → os novos FAIL.
- [ ] **Step 3:** Implementar. `ATRIBUTOS_PERMITIDOS` vira função `(tag, nome, valor) -> bool` (bleach aceita callable) com as regras acima, mantendo as de `a` e `img`. No callback de linkify, se o `href` começar com `#`, devolver `attrs` sem mexer.
- [ ] **Step 4:** `python manage.py test conteudo` → PASS.
- [ ] **Step 5: Conferir diff.**

---

### Task 3: Página do artigo, listas, prévia de link e CSS

**Files:**
- Modify: `templates/conteudo/artigo_detail.html`, `templates/conteudo/artigo_list.html`, template da página inicial (o que tem o laço `artigos_recentes`, em `templates/core/`)
- Modify: `conteudo/views.py` (`ArtigoDetailView.get_context_data`)
- Modify: `core/context_processors.py` (`seo` passa a entregar `seo_imagem_alt`), `templates/base.html` (`og:image:alt` usa `{{ seo_imagem_alt }}`)
- Modify: `static/css/site.css`
- Test: `conteudo/tests.py`

**Interfaces:**
- Consumes: campos da Task 1; filtros `tempo_leitura`, `capa_url` da Task 2.
- Produces: contexto `seo_imagem_alt` (padrão: o texto atual de `og:image:alt`); na página do artigo com capa, `seo_imagem` = URL absoluta da capa e `seo_imagem_alt` = `capa_alt`.

Ordem no `artigo_detail.html` (do spec): selo de categoria → título (`h1`) → linha fina (`resumo`, classe `fq-linha-fina`) → linha de metadados (`Por Marcos Vinicius Pagliarini` · `Publicado em DD/MM/AAAA` · `N min de leitura`) → nota de IA só se `com_apoio_ia` → régua → `<figure class="fq-capa">` com `img` (`alt=capa_alt`) e `figcaption` com `capa_credito`, só se `capa_url` não vazio → corpo. Quadros, sumário, lide, glossário e fontes vêm dentro do corpo.

Listas (artigos e página inicial): miniatura da capa no topo do card (`card-img-top`, proporção 1200:630, `loading="lazy"`, `alt=capa_alt`) só quando houver.

CSS: classes `.fq-linha-fina`, `.fq-artigo-meta`, `.fq-nota-ia`, `.fq-capa`, e dentro de `.fq-artigo-corpo`: `aside` (borda 1px `--fq-rule`, borda esquerda 4px `--fq-teal`, fundo `--fq-paper-raised`), título do quadro via `h4` já existente, variações `.fq-sumario` (sem borda colorida, lista em linha), `.fq-glossario` (`dt` em negrito), e `scroll-margin-top` nos `h2[id]` para a navbar não cobrir o título. Conferir o seletor do lide (`> p:first-of-type`): continua pegando o primeiro `p` direto do corpo, e os `p` dentro de `aside` não entram nele.

- [ ] **Step 1: Escrever os testes que falham** (nova `PaginaArtigoTests`; staff logado ou artigos publicados)

```python
def test_artigo_feito_com_ia_mostra_nota(self):
    criar_artigo('com-ia'); Artigo.objects.filter(slug='com-ia').update(com_apoio_ia=True)
    r = self.client.get(reverse('conteudo:detalhe', args=['com-ia']))
    self.assertContains(r, 'Por Marcos Vinicius Pagliarini')
    self.assertContains(r, 'Pesquisa e redação com apoio de IA, revisado pelo autor.')

def test_artigo_sem_ia_mostra_so_autoria(self):
    criar_artigo('sem-ia')
    r = self.client.get(reverse('conteudo:detalhe', args=['sem-ia']))
    self.assertContains(r, 'Por Marcos Vinicius Pagliarini')
    self.assertNotContains(r, 'apoio de IA')

def test_mostra_tempo_de_leitura(self):
    criar_artigo('tempo', corpo='<p>' + 'palavra ' * 401 + '</p>')
    self.assertContains(self.client.get(reverse('conteudo:detalhe', args=['tempo'])), '3 min de leitura')

def test_capa_aparece_com_credito_e_vira_previa_do_link(self):
    criar_artigo('capa'); Artigo.objects.filter(slug='capa').update(
        capa='img/previa.png', capa_alt='Moedas', capa_credito='Foto: Fulano / Unsplash')
    r = self.client.get(reverse('conteudo:detalhe', args=['capa']))
    self.assertContains(r, 'alt="Moedas"')
    self.assertContains(r, 'Foto: Fulano / Unsplash')
    self.assertEqual(r.context['seo_imagem'], 'http://testserver/static/img/previa.png')
    self.assertEqual(r.context['seo_imagem_alt'], 'Moedas')

def test_artigo_sem_capa_mantem_previa_padrao(self):
    criar_artigo('sem-capa')
    r = self.client.get(reverse('conteudo:detalhe', args=['sem-capa']))
    self.assertNotContains(r, 'fq-capa')
    self.assertTrue(r.context['seo_imagem'].endswith('img/previa.png'))

def test_lista_mostra_miniatura_so_com_capa(self):
    criar_artigo('a'); criar_artigo('b')
    Artigo.objects.filter(slug='a').update(capa='img/previa.png', capa_alt='Capa A')
    r = self.client.get(reverse('conteudo:lista'))
    self.assertContains(r, 'alt="Capa A"', count=1)
```

(`img/previa.png` é usado como capa nos testes porque já existe em `static/`.)

- [ ] **Step 2:** `python manage.py test conteudo` → os novos FAIL.
- [ ] **Step 3:** Implementar templates, view, context processor e `base.html`.
- [ ] **Step 4:** Escrever o CSS.
- [ ] **Step 5:** `python manage.py test` (projeto inteiro, por causa do context processor) → PASS. `python manage.py check` → sem erros.
- [ ] **Step 6: Conferência visual.** Criar no banco local um artigo de teste com capa e todos os quadros (o artigo de exemplo do spec, "Selic: o que é e por que ela mexe no seu bolso", com texto curto), abrir `/artigos/<slug>/` com `runserver` nos temas claro e escuro e em largura de celular (~375 px). Conferir: lide em destaque, quadros legíveis, sumário levando às seções sem a navbar cobrir o título, capa sem distorção. Apagar o artigo de teste depois.
- [ ] **Step 7: Conferir diff.**

---

### Task 4: `importar_artigo` com capa e nota de IA

**Files:**
- Modify: `conteudo/management/commands/importar_artigo.py`
- Test: `conteudo/tests.py`

**Interfaces:**
- Consumes: campos da Task 1.
- Produces: JSON aceito = `{"titulo", "resumo", "corpo", "categoria"}` obrigatórios + opcionais `"capa"`, `"capa_alt"`, `"capa_credito"`, `"com_apoio_ia"` (bool, padrão `false`). Se `capa` vier, `capa_alt` e `capa_credito` passam a ser obrigatórios.

Validação da capa: o caminho é relativo a `static/`; recusar caminho absoluto ou com `..`; achar o arquivo com `django.contrib.staticfiles.finders.find(capa)`; abrir com Pillow e exigir formato JPEG, PNG ou WEBP e tamanho exato 1200×630. Mensagens de erro em pt-BR dizendo o campo e o problema (ex.: `"capa" tem 1600x900 px; o tamanho exigido é 1200x630.`). Limites: `capa_alt` 200, `capa_credito` 300.

- [ ] **Step 1: Escrever os testes que falham** (nova `ImportarArtigoTests`; JSON gravado em `tempfile`; imagens de teste geradas com Pillow numa pasta temporária colocada em `STATICFILES_DIRS` via `override_settings`)

```python
def test_importa_com_capa_valida(self):
    # capa 1200x630 em <tmp>/img/artigos/t/capa.jpg
    call_command('importar_artigo', self.json(capa='img/artigos/t/capa.jpg', capa_alt='Moedas', capa_credito='Foto: X / Pexels', com_apoio_ia=True))
    a = Artigo.objects.get()
    self.assertEqual((a.capa, a.com_apoio_ia, a.status), ('img/artigos/t/capa.jpg', True, Artigo.Status.RASCUNHO))

def test_sem_capa_continua_funcionando(self):  # regressão
    call_command('importar_artigo', self.json())
    self.assertFalse(Artigo.objects.get().com_apoio_ia)

def test_recusa_capa_inexistente(self):
    with self.assertRaisesMessage(CommandError, '"capa"'):
        call_command('importar_artigo', self.json(capa='img/artigos/t/nao.jpg', capa_alt='a', capa_credito='c'))
    self.assertFalse(Artigo.objects.exists())

def test_recusa_capa_com_tamanho_errado(self):  # imagem 1600x900
    with self.assertRaisesMessage(CommandError, '1200x630'): ...

def test_recusa_caminho_com_ponto_ponto(self):
    with self.assertRaisesMessage(CommandError, '"capa"'):
        call_command('importar_artigo', self.json(capa='../config/settings.py', capa_alt='a', capa_credito='c'))

def test_capa_exige_credito_e_alt(self):
    with self.assertRaisesMessage(CommandError, '"capa_credito"'): ...
```

- [ ] **Step 2:** `python manage.py test conteudo.tests.ImportarArtigoTests` → FAIL.
- [ ] **Step 3:** Implementar. Atualizar o `help` do comando.
- [ ] **Step 4:** `python manage.py test conteudo` → PASS.
- [ ] **Step 5: Conferir diff.**

---

### Task 5: Comando `exportar_artigo_migracao`

**Files:**
- Create: `conteudo/management/commands/exportar_artigo_migracao.py`
- Test: `conteudo/tests.py`

**Interfaces:**
- Consumes: campos da Task 1.
- Produces: `python manage.py exportar_artigo_migracao <slug> [--pasta CAMINHO]` → grava `NNNN_importa_artigo_<slug-curto>.py` na pasta de migrações do `conteudo` (ou em `--pasta`, usada nos testes) e imprime o caminho. `NNNN` = número da folha atual + 1, com 4 dígitos; `<slug-curto>` = slug com `-` trocado por `_`, cortado em 40 caracteres. A dependência é a folha atual do app `conteudo`, lida com `django.db.migrations.loader.MigrationLoader(None, ignore_no_migrations=True).graph.leaf_nodes()` filtrado por `conteudo` (se houver mais de uma folha, `CommandError` pedindo para resolver antes).

O arquivo gerado segue o formato de `0004_importa_artigo_galipolo.py`: um dicionário `ARTIGO` com `titulo, slug, resumo, corpo, categoria, capa, capa_alt, capa_credito, com_apoio_ia` e `status='RASCUNHO'` (sempre rascunho, mesmo que o local esteja publicado), valores escritos com `repr()`; `importar_artigo` faz `get_or_create(slug=..., defaults=ARTIGO)`; `remover_artigo` apaga pelo slug. Cabeçalho com comentário em pt-BR: de onde veio e que o autor publica pelo Admin de produção.

- [ ] **Step 1: Escrever os testes que falham** (nova `ExportarArtigoMigracaoTests`, com `--pasta` num `tempfile.TemporaryDirectory`)

```python
CORPO_DIFICIL = '<p>Aspas "duplas", \'simples\', acentuação — e barra \\ e\nquebra.</p>'

def test_gera_arquivo_com_numero_e_dependencia_da_folha(self):
    criar_artigo('selic-o-que-e')
    call_command('exportar_artigo_migracao', 'selic-o-que-e', pasta=self.tmp)
    nome = os.listdir(self.tmp)[0]
    self.assertRegex(nome, r'^\d{4}_importa_artigo_selic_o_que_e\.py$')
    folha = ...  # nome da folha atual do conteudo, via MigrationLoader
    self.assertIn(f"('conteudo', '{folha}')", self.ler(nome).replace('"', "'"))

def test_ida_e_volta_preserva_os_campos(self):
    criar_artigo('dificil', corpo=CORPO_DIFICIL)
    Artigo.objects.filter(slug='dificil').update(capa='img/x.jpg', capa_alt='A', capa_credito='Foto: B', com_apoio_ia=True)
    modulo = self.gerar_e_importar('dificil')  # importlib a partir do arquivo gerado
    self.assertEqual(modulo.ARTIGO['corpo'], CORPO_DIFICIL)
    self.assertEqual(modulo.ARTIGO['status'], 'RASCUNHO')
    self.assertTrue(modulo.ARTIGO['com_apoio_ia'])

def test_importar_nao_duplica_slug_existente(self):
    criar_artigo('ja-existe')
    modulo = self.gerar_e_importar('ja-existe')
    modulo.importar_artigo(django_apps, None)
    self.assertEqual(Artigo.objects.filter(slug='ja-existe').count(), 1)

def test_remover_apaga_so_esse_slug(self):
    criar_artigo('fica'); criar_artigo('sai')
    modulo = self.gerar_e_importar('sai')
    modulo.remover_artigo(django_apps, None)
    self.assertEqual(list(Artigo.objects.values_list('slug', flat=True)), ['fica'])

def test_slug_inexistente_da_erro(self):
    with self.assertRaisesMessage(CommandError, 'nao-existe'):
        call_command('exportar_artigo_migracao', 'nao-existe', pasta=self.tmp)
```

(`django_apps` = `django.apps.apps`, que expõe `get_model` como o `apps` histórico.)

- [ ] **Step 2:** `python manage.py test conteudo.tests.ExportarArtigoMigracaoTests` → FAIL.
- [ ] **Step 3:** Implementar.
- [ ] **Step 4:** `python manage.py test conteudo` → PASS. Gerar uma migração de verdade para um artigo do banco local numa pasta temporária e conferir que `python -c "import ast; ast.parse(open(...).read())"` passa e que o arquivo lido por um humano faz sentido. Não gravar em `conteudo/migrations/`.
- [ ] **Step 5: Conferir diff.**

---

### Task 6: Reescrever a skill e atualizar a documentação

**Files:**
- Modify: `C:\Users\pagli\Desktop\Meus Projetos Claude\Minhas skills\formatar-artigo\SKILL.md` (outro repositório)
- Modify: `CLAUDE.md` do portal (seções `conteudo/` e "Identidade visual")
- Modify: `.gitignore` do portal (acrescentar `.superpowers/`)

**Interfaces:**
- Consumes: JSON do `importar_artigo` (Task 4), `exportar_artigo_migracao` (Task 5), classes `fq-em-30s`, `fq-sumario`, `fq-na-pratica`, `fq-glossario`, `dl/dt/dd`, `h2 id` (Task 2).

Conteúdo da skill (o fluxo e as regras vêm do spec; aqui só o que o implementador não pode adivinhar):

- **Frontmatter:** `name: formatar-artigo`; `description` em pt-BR no padrão "Use quando…", cobrindo: pedir um artigo sobre um tema para o Portal FinQuant ("escreve um artigo sobre X", "artigo do site sobre X", "quero um artigo sobre X") e o caso antigo de transformar links em artigo.
- **Passos 1–8 do spec**, com as pausas explícitas: o passo 4 espera o "aprovado" do autor; o passo 8 termina com a pergunta (via `AskUserQuestion`) sobre o caminho até a produção.
- **Critérios de fonte** (do spec), com os selos e as exclusões; 4 a 8 fontes; descartadas com motivo.
- **Formato da proposta de curadoria** (passo 3) como modelo em Markdown, para ficar igual toda vez.
- **Modelo de corpo HTML** com a estrutura do spec, usando só as tags aceitas: `aside.fq-em-30s` (com `h4` "Em 30 segundos" e `ul`) → `aside.fq-sumario` (`h4` "Neste artigo" e `ol` de links `#id`) → lide `p` → seções `h2 id="..."` em forma de pergunta → `aside.fq-na-pratica` (`h4` "Na prática", conta passo a passo) → `aside.fq-glossario` (`h4` "Glossário" e `dl`) → `h3` "Para saber mais" (link interno do portal, se houver) → `h3` "Fontes" com `ol` numerada, cada item com veículo, título, data DD/MM/AAAA e link. O lide precisa ser o **primeiro `p` direto do corpo** (os quadros acima dele usam `aside`, por isso não roubam o destaque).
- **Tom:** leve e popular, frases curtas, termos técnicos explicados na primeira aparição; sem recomendação de investimento; sem sensacionalismo.
- **Capa:** buscar em Unsplash ou Pexels; baixar já recortada em 1200×630 (Unsplash: parâmetros `?w=1200&h=630&fit=crop&fm=jpg`; Pexels: `?auto=compress&cs=tinysrgb&w=1200&h=630&fit=crop`); conferir o tamanho com Pillow; gravar em `static/img/artigos/<slug>/capa.jpg`; `capa_credito` no formato `Foto: <Nome> / Unsplash` (ou Pexels).
- **Imagens das fontes:** só gráficos de órgãos públicos ou licença livre, com crédito em `figcaption`; de jornal, só link nas fontes ("veja o gráfico original") ou gráfico refeito com os dados públicos.
- **Verificação (passo 6)** como checklist: cada número ↔ fonte; contas do "Na prática" refeitas; ortografia; datas DD/MM/AAAA; só tags aceitas; título ≤ 200 e resumo ≤ 300 caracteres; `com_apoio_ia: true` no JSON.
- **Passo 7:** JSON no scratchpad da sessão, `python manage.py importar_artigo <json>`.
- **Passo 8:** relatar slug, prévia local (`runserver` + `/artigos/<slug>/`, logado como staff), Admin local, lista de imagens com crédito e licença. Quando o autor aprovar e **pedir o commit**: `python manage.py exportar_artigo_migracao <slug>`, e o commit leva a migração e a pasta `static/img/artigos/<slug>/` juntas. Lembrar que o artigo nasce como rascunho em produção e é publicado pelo Admin de produção.
- **Erros comuns:** os atuais, atualizados (classe fora da lista em `aside`, lide que não é o primeiro `p`, capa fora de 1200×630, imagem de jornal colada, número sem fonte, commit sem a pasta de imagens).

`CLAUDE.md` do portal: na linha do `conteudo/`, citar os campos novos, os dois comandos e o caminho até a produção pela migração gerada; em "Identidade visual", registrar a exceção da foto de capa (decisão do autor, 10/11/2026).

- [ ] **Step 1:** Reescrever o `SKILL.md`.
- [ ] **Step 2: Conferir a skill contra o código:** cada classe, tag, campo do JSON e nome de comando citados na skill existe e está escrito igual no código das Tasks 2, 4 e 5 (`grep` de cada nome).
- [ ] **Step 3:** Atualizar `CLAUDE.md` e `.gitignore` do portal.
- [ ] **Step 4:** Revisão ortográfica de todo texto novo (skill, `CLAUDE.md`, mensagens dos comandos, textos dos templates).
- [ ] **Step 5:** `python manage.py test` e `python manage.py check` → PASS. `git diff --numstat` nos dois repositórios.
- [ ] **Step 6:** Relatar ao autor o que ficou sem commit nos dois repositórios (portal e `Minhas skills/formatar-artigo`) e lembrar que a skill nova só carrega numa sessão nova.

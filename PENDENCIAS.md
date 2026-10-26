# Pendências de Portal FinQuant

Melhorias e correções previstas. Cada item tem uma linha no banco 💡 Sugestões do Centro de Comando. Executado → Implementada no banco e o item sai daqui.

## App estudo_caso
**Sugestão:** https://www.notion.so/3fdd653a12cb81309b80c037ccb7851c · **Registrado em:** 18/10/2026 · **Origem:** Planejada

Do `README.md` ("Próximos passos (fase 2)"): App `estudo_caso`: comparação de uma estratégia ativa de compra de ações brasileiras (análise técnica + fundamentalista) com renda fixa e investimento passivo, usando pandas/numpy/yfinance.

## Exportar as avaliações para a análise de qualidade
**Sugestão:** https://www.notion.so/3fdd653a12cb8127af26d5cfba4f775b · **Registrado em:** 18/10/2026 · **Origem:** Planejada

Do `README.md` ("Próximos passos (fase 2)"): Exportação dos dados de `avaliacoes` (via `pandas`) para a análise de qualidade do projeto na entrega final do TCC.

## Atalhos neon quebrados em .claude/skills
**Sugestão:** https://www.notion.so/3fdd653a12cb812895e2f65a09fc67f9 · **Registrado em:** 18/10/2026 · **Origem:** Manual

Os atalhos `neon` e `neon-postgres` em `.claude/skills/` apontam para `Desktop\Projeto - Portal FinQuant\.agents/skills/`, pasta que não existe mais (o projeto mudou para `Projeto Final ADS\Portal FinQuant`). Achado na revisão do plano de organização por temas (18/10/2026). Tratar no inventário de caminhos de 19 a 24/10/2026: achar onde está hoje `.agents/skills/neon` e refazer os dois atalhos, ou removê-los se o plugin neon global já cobrir.

## LGPD e consentimento no formulário de avaliação
**Sugestão:** https://www.notion.so/405d653a12cb81daa4e4fcc5315d3dd9 · **Registrado em:** 26/10/2026 · **Origem:** Manual

O formulário coleta sexo, faixa etária e renda familiar sem aviso de privacidade nem caixa de concordância (`templates/avaliacoes/avaliacao_form.html`). Incluir os dois e confirmar com o orientador se a UNISINOS exige TCLE. Achado na revisão completa de 26/10/2026.

## Evitar avaliações duplicadas
**Sugestão:** https://www.notion.so/405d653a12cb817b9823c198cb7184f6 · **Registrado em:** 26/10/2026 · **Origem:** Manual

A mesma pessoa pode avaliar várias vezes, logada ou não, o que distorce as médias do TCC. Limitar a uma avaliação por usuário logado, marcar a sessão dos anônimos e filtrar duplicadas na exportação. Achado na revisão completa de 26/10/2026.

## Aviso de avaliação no celular
**Sugestão:** https://www.notion.so/405d653a12cb8119b8edf40283198b30 · **Registrado em:** 26/10/2026 · **Origem:** Manual

O aviso "Antes de você ir" (`templates/avaliacoes/_modal_exit_intent.html`) depende do mouse sair da janela e nunca aparece no celular. Disparar também por tempo na página ou depois de usar um simulador. Achado na revisão completa de 26/10/2026.

## Teto da Lei 14.690/2023 no simulador de dívida do cartão
**Sugestão:** https://www.notion.so/405d653a12cb8137af94cbe4d26e6ed6 · **Registrado em:** 26/10/2026 · **Origem:** Manual

Desde 01/2024, juros e encargos do rotativo não podem passar de 100% do valor original da dívida; o simulador mostra um "nunca quita" que cresce por 600 meses. Aplicar o teto (ou explicá-lo no painel "Como calculamos isso?") e citar a regra que leva a dívida ao parcelamento após 30 dias. Achado na revisão completa de 26/10/2026.

## Taxa ao mês ou ao ano nos simuladores
**Sugestão:** https://www.notion.so/405d653a12cb8124b4b2e8f62febb6ea · **Registrado em:** 26/10/2026 · **Origem:** Manual

Leigos conhecem a taxa ao ano (CDI, Selic, poupança). Adicionar um seletor "ao mês / ao ano" em `simuladores/forms.py`, com a conversão (1 + a)^(1/12) − 1. Achado na revisão completa de 26/10/2026.

## Avisos de conteúdo educacional e de valores nominais
**Sugestão:** https://www.notion.so/405d653a12cb81649269cf50ea16ea54 · **Registrado em:** 26/10/2026 · **Origem:** Manual

Rodapé do `base.html` sem o aviso "conteúdo educacional, não é recomendação de investimento", e simuladores sem a nota de que os valores são nominais, sem IR e sem inflação. Achado na revisão completa de 26/10/2026.

## Data de publicação real dos artigos
**Sugestão:** https://www.notion.so/405d653a12cb81db81f0c4ff6c124b5f · **Registrado em:** 26/10/2026 · **Origem:** Manual

`Artigo.publicado_em` usa `auto_now_add` e guarda a data de criação: um rascunho publicado depois aparece com a data antiga. Gravar a data quando o status muda para Publicado (admin e ação "Marcar como publicado"). Achado na revisão completa de 26/10/2026.

## Cadastro e login mantendo o que foi digitado
**Sugestão:** https://www.notion.so/405d653a12cb8152be51db15eacf60bd · **Registrado em:** 26/10/2026 · **Origem:** Manual

Os campos de `contas/login.html` e `contas/cadastro.html` são montados sem `value`, e o usuário redigita tudo depois de um erro. O cadastro também não pede e-mail, então não há recuperação de senha. Achado na revisão completa de 26/10/2026.

## Gráfico dos simuladores num arquivo só
**Sugestão:** https://www.notion.so/405d653a12cb8148a2d8d94c232133e0 · **Registrado em:** 26/10/2026 · **Origem:** Manual

O bloco de JS/CSS do gráfico SVG se repete nos três templates de `templates/simuladores/` (cerca de 400 linhas cada). Extrair para `static/js/grafico.js` e atualizar o "Padrão dos simuladores" do `CLAUDE.md` junto. Achado na revisão completa de 26/10/2026.

## Testes dos apps conteudo e core
**Sugestão:** https://www.notion.so/405d653a12cb81558e07e63ec782976c · **Registrado em:** 26/10/2026 · **Origem:** Manual

`conteudo/tests.py` e `core/tests.py` estão vazios. Cobrir ao menos: rascunho invisível para quem não é da equipe e o filtro `corpo_seguro` removendo `<script>`. Achado na revisão completa de 26/10/2026.

## Ajustes menores
**Sugestão:** https://www.notion.so/405d653a12cb8119bb7eed2476401967 · **Registrado em:** 26/10/2026 · **Origem:** Manual

Fixar `PYTHON_VERSION` no `render.yaml`; `try/catch` no acesso ao `localStorage` do tema (`base.html`); páginas 404 e 500 com a identidade do site; filtro por categoria na lista de artigos. Achado na revisão completa de 26/10/2026.

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

## Data de publicação real dos artigos
**Sugestão:** https://www.notion.so/405d653a12cb81db81f0c4ff6c124b5f · **Registrado em:** 26/10/2026 · **Origem:** Manual

`Artigo.publicado_em` usa `auto_now_add` e guarda a data de criação: um rascunho publicado depois aparece com a data antiga. Gravar a data quando o status muda para Publicado (admin e ação "Marcar como publicado"). Achado na revisão completa de 26/10/2026.

## Gráfico dos simuladores num arquivo só
**Sugestão:** https://www.notion.so/405d653a12cb8148a2d8d94c232133e0 · **Registrado em:** 26/10/2026 · **Origem:** Manual

O bloco de JS/CSS do gráfico SVG se repete nos três templates de `templates/simuladores/` (cerca de 400 linhas cada). Extrair para `static/js/grafico.js` e atualizar o "Padrão dos simuladores" do `CLAUDE.md` junto. Achado na revisão completa de 26/10/2026.

## Ajustes menores
**Sugestão:** https://www.notion.so/405d653a12cb8119bb7eed2476401967 · **Registrado em:** 26/10/2026 · **Origem:** Manual

Fixar `PYTHON_VERSION` no `render.yaml`; `try/catch` no acesso ao `localStorage` do tema (`base.html`); páginas 404 e 500 com a identidade do site; filtro por categoria na lista de artigos. Achado na revisão completa de 26/10/2026.

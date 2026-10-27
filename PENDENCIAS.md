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


## Gráfico dos simuladores num arquivo só
**Sugestão:** https://www.notion.so/405d653a12cb8148a2d8d94c232133e0 · **Registrado em:** 26/10/2026 · **Origem:** Manual

O bloco de JS/CSS do gráfico SVG se repete nos três templates de `templates/simuladores/` (cerca de 400 linhas cada). Extrair para `static/js/grafico.js` e atualizar o "Padrão dos simuladores" do `CLAUDE.md` junto. Achado na revisão completa de 26/10/2026.


## Recuperação de senha por e-mail
**Sugestão:** https://www.notion.so/405d653a12cb8199b61fe43fcf85fab7 · **Registrado em:** 26/10/2026 · **Origem:** Manual

O cadastro pede e-mail desde 26/10/2026, mas não há tela de "esqueci a senha": produção usa o backend de e-mail do console (`MAILERS` em `config/settings.py`). Configurar um SMTP (credenciais no painel do Render) e ligar as views de reset de senha do Django.

## Apagar o Postgres antigo do Render
**Sugestão:** https://www.notion.so/405d653a12cb81e4809dcf0eab305c3e · **Registrado em:** 26/10/2026 · **Origem:** Manual

O banco `portal-finquant-db` do Render está sem uso desde a migração para o Neon (28/08/2026) e saiu do `render.yaml` em 26/10/2026. Apagar pelo painel do Render depois de confirmar que a `DATABASE_URL` do serviço aponta para o Neon.

# Pendências de Portal FinQuant

Melhorias e correções previstas. Cada item tem uma linha no banco 💡 Sugestões do Centro de Comando. Executado → Implementada no banco e o item sai daqui.

## App estudo_caso
**Sugestão:** https://www.notion.so/3fdd653a12cb81309b80c037ccb7851c · **Registrado em:** 18/10/2026 · **Origem:** Planejada

Do `README.md` ("Próximos passos (fase 2)"): App `estudo_caso`: comparação de uma estratégia ativa de compra de ações brasileiras (análise técnica + fundamentalista) com renda fixa e investimento passivo, usando pandas/numpy/yfinance.

**Base (27/10/2026):** o app vai ser construído a partir do projeto `Script Analise Quantitativa` (pasta irmã, em `Desktop\Projeto Final ADS\`). A análise sai desse script e é levada para o portal; não se começa do zero.

**No ar (09/11/2026):** app `estudo_caso` em `/estudo-caso/` ("Análise de ações" no menu), no `main` e no Render. Deploy Hook e secret `RENDER_DEPLOY_HOOK` configurados; o workflow semanal foi testado e disparou o deploy. Tempos medidos no Render: 1 ação 15 s, 4 ações 33 s, seleção automática ~75 s (textos de `execucao.tempo_previsto` ajustados). Falta só: abrir o resumo em PDF do Render e conferir os símbolos ✓ e − (o PDF já sai, 200, 70 KB).

## Conferir a 1ª rodada completa do pré-cálculo das análises (14/11/2026)
**Sugestão:** https://www.notion.so/413d653a12cb814894aad42acd4e59bd · **Registrado em:** 09/11/2026 · **Origem:** Manual

O pré-cálculo de madrugada (02:00–05:00, `estudo_caso/execucao.py`) foi ligado em 09/11/2026, depois de um teste aprovado no Render. No sábado, 14/11/2026, o deploy da 01:00 traz preços novos e a rodada das 02:00 refaz as 136 análises (60 seleções automáticas + 76 ações sozinhas). Conferir: (1) abrir uma amostra de análises (devem abrir prontas, com a data nova); (2) o histórico do UptimeRobot entre 02:00 e 05:00, para garantir que o site não travou. Os logs do Render gratuito só guardam 1 hora; se houver travamento, o `estudo_caso/vigia.py` grava a pilha das threads no log.

## Investigar o tempo de resposta de Entrar e Cadastro (~1 s)
**Sugestão:** https://www.notion.so/413d653a12cb81e3aa4ef557d674cc6b · **Registrado em:** 09/11/2026 · **Origem:** Manual

No teste de tempo de 09/11/2026 em produção, Entrar e Cadastro levaram ~0,95 s, contra ~0,24 s das páginas que não leem o banco. Hipótese a conferir: a distância entre o servidor (Render, Oregon) e o banco (Neon, São Paulo). Passos: contar as consultas de cada página e, se a hipótese se confirmar, avaliar mudar a região de um dos dois.

**Tempos de referência (09/11/2026, produção no commit `bd84573`, sem as abas; mediana de 3 acessos):** simuladores (índice, os 3 e o cálculo POST), Esqueci a senha, Avaliação e Análise de ações passo 1: 0,23 a 0,25 s · Início 0,58 s (1º acesso 1,7 s) · Artigo 0,61 s · Artigos 0,76 s · Entrar e Cadastro ~0,95 s · telas da análise PETR4 (0 a 9) 0,9 a 1,5 s · resumo em PDF 2,6 s. Análises: padrão PETR4 e seleção automática já prontas no cache, 1,3 a 1,6 s (a automática levava ~75 s sem cache); 1 ação nova (WEGE3) 15,2 s; 4 ações novas (ITUB4, BBDC4, ABEV3, WEGE3) 26,9 s; página inicial durante o cálculo: mediana 0,64 s, máximo 1,13 s. Essas duas análises novas ficaram no cache: num próximo teste, use outras ações ou opções. Para repetir: `python scripts/medir_tempos.py resultado.json`.

**2ª rodada (09/11/2026, versão com abas, commit `3c3cafe`):** páginas iguais à 1ª (variação de até 0,05 s); telas da análise 0,95 a 1,7 s; PDF novo 3,1 s (71 KB); padrão PETR4 e automática no cache 1,0 e 1,5 s; 1 ação nova (VALE3) 16,9 s; 4 ações novas (PETR4, VALE3, ITUB4, BBAS3) 32,7 s; página inicial durante o cálculo: mediana 0,65 s, máximo 1,94 s. Também ficaram no cache.

**10 ações escolhidas uma a uma (09/11/2026, padrões do site):** B3SA3, RENT3, SUZB3, GGBR4, RADL3, LREN3, EQTL3, PRIO3, TOTS3, SBSP3 em 37,0 s e ITSA4, BBSE3, CMIG4, CPFE3, KLBN11, UGPA3, VIVT3, TIMS3, CSAN3, HYPE3 em 35,7 s; a etapa "testes" leva ~20 s desse total. Telas 0,8 a 2,6 s (até 152 KB); PDF 1,7 a 2,5 s. Página inicial durante o cálculo: mediana 0,72 s, máximo 1,90 s. Na 1ª rodada, um acesso levou 55 s, quase com certeza a troca de versão do deploy disparado às 20:02 (não se repetiu na 2ª). A estimativa da tela de espera de 2 a 10 ações passou a "menos de 1 minuto". As duas carteiras ficaram no cache.

## Exportar as avaliações para a análise de qualidade
**Sugestão:** https://www.notion.so/3fdd653a12cb8127af26d5cfba4f775b · **Registrado em:** 18/10/2026 · **Origem:** Planejada

Do `README.md` ("Próximos passos (fase 2)"): Exportação dos dados de `avaliacoes` (via `pandas`) para a análise de qualidade do projeto na entrega final do TCC.

**Sequência (27/10/2026):** as avaliações ainda não foram abertas ao público, então não há dados para exportar. Ordem: (1) terminar o portal, incluindo o `estudo_caso`; (2) enviar o portal para as pessoas avaliarem; (3) só depois exportar e analisar os dados de `avaliacoes`.

## Recuperação de senha por e-mail
**Sugestão:** https://www.notion.so/405d653a12cb8199b61fe43fcf85fab7 · **Registrado em:** 26/10/2026 · **Origem:** Manual

O cadastro pede e-mail desde 26/10/2026, mas não há tela de "esqueci a senha": produção usa o backend de e-mail do console (`MAILERS` em `config/settings.py`). Configurar um SMTP (credenciais no painel do Render) e ligar as views de reset de senha do Django.

**Código pronto (27/10/2026):** telas de "esqueci a senha" em `/contas/esqueci-a-senha/` e SMTP lido do ambiente (`EMAIL_HOST` e afins, veja `.env.example`). As variáveis do Gmail foram preenchidas no Render em 27/10/2026.

**Bloqueio (27/10/2026):** o envio falha com `OSError: [Errno 101] Network is unreachable` porque o plano gratuito do Render bloqueia a saída nas portas SMTP (25, 465 e 587) desde setembro de 2025 ([changelog do Render](https://render.com/changelog/free-web-services-will-no-longer-allow-outbound-traffic-to-smtp-ports)). Não é erro de código nem de credencial. A tela continua respondendo "confira o seu e-mail", e a falha só aparece no log do Render ("Failed to send password reset email"). Decisão de 27/10/2026: ficar sem envio por enquanto; quem esquecer a senha pede ao admin, que troca pelo `/admin/`. Para retomar, escolher entre (1) um serviço de e-mail por API HTTPS, como o Brevo (gratuito, 300 e-mails/dia, aceita o Gmail como remetente), com `django-anymail`, ou (2) o plano pago do Render (Starter, cerca de US$ 7/mês), que libera o SMTP sem mudar o código. Enquanto isso, a tela de "esqueci a senha" mostra um aviso para falar com o administrador; ao retomar, ligar `RECUPERACAO_SENHA_ATIVA=True` no Render.

## Procedência e lacunas nos dados
**Sugestão:** https://www.notion.so/40ad653a12cb81c5baa1da65238fb42e · **Registrado em:** 31/10/2026 · **Origem:** Manual

Padrão do Mapa de Feminicídio (`Portfólio/docs/referencias/mapafeminicidio-josyscript-com.md`): cada série ou indicador mostra fonte, data da coleta e, se possível, o hash do arquivo baixado; "sem dado" nunca vira zero nem repete o último valor sem aviso; período parcial avisado ("até setembro"); dados oficiais (B3, CVM, BCB) e cálculos derivados (retorno, volatilidade) com rótulo próprio, sem somar bases diferentes; frase curta de método junto de cada número. Serve também para o capítulo de metodologia do TCC. Encaixa junto com o app `estudo_caso`.

## Ver tabela ao lado dos gráficos e estado da tela na URL
**Sugestão:** https://www.notion.so/40ad653a12cb81ea8647fb2a5dee5889 · **Registrado em:** 31/10/2026 · **Origem:** Manual

Botão "Ver tabela" em cada gráfico (acessibilidade e conferência) e ativo, período e indicador guardados na URL, para compartilhar uma análise. **Andamento (09/11/2026):** a análise de ações (`estudo_caso`) já guarda as escolhas e a tela na URL; falta o "Ver tabela". Referência: `Portfólio/docs/referencias/mapafeminicidio-josyscript-com.md`.

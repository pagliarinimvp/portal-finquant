# Pendências de Portal FinQuant

Melhorias e correções previstas. Cada item tem uma linha no banco 💡 Sugestões do Centro de Comando. Executado → Implementada no banco e o item sai daqui.

## Conferir a 1ª rodada completa do pré-cálculo das análises (14/11/2026)
**Sugestão:** https://www.notion.so/413d653a12cb814894aad42acd4e59bd · **Registrado em:** 09/11/2026 · **Origem:** Manual

O pré-cálculo de madrugada (02:00–05:00, `estudo_caso/execucao.py`) foi ligado em 09/11/2026, depois de um teste aprovado no Render. No sábado, 14/11/2026, o deploy da 01:00 traz preços novos e a rodada das 02:00 refaz as 136 análises (60 seleções automáticas + 76 ações sozinhas). Conferir: (1) abrir uma amostra de análises (devem abrir prontas, com a data nova); (2) o histórico do UptimeRobot entre 02:00 e 05:00, para garantir que o site não travou. Os logs do Render gratuito só guardam 1 hora; se houver travamento, o `estudo_caso/vigia.py` grava a pilha das threads no log.

## Exportar as avaliações para a análise de qualidade
**Sugestão:** https://www.notion.so/3fdd653a12cb8127af26d5cfba4f775b · **Registrado em:** 18/10/2026 · **Origem:** Planejada

Do `README.md` ("Próximos passos (fase 2)"): Exportação dos dados de `avaliacoes` (via `pandas`) para a análise de qualidade do projeto na entrega final do TCC.

**Sequência (27/10/2026):** as avaliações ainda não foram abertas ao público, então não há dados para exportar. Ordem: (1) terminar o portal, incluindo o `estudo_caso`; (2) enviar o portal para as pessoas avaliarem; (3) só depois exportar e analisar os dados de `avaliacoes`.

## Revisar os números dos artigos depois de cada reunião do Copom
**Sugestão:** https://www.notion.so/414d653a12cb811b81dbd14d434c368f · **Registrado em:** 10/11/2026 · **Origem:** Manual

As versões novas dos artigos (rascunhos de 10/11/2026) citam a Selic de 04/11/2026 (13,75%) e o Focus de 06/11/2026. Depois de cada reunião do Copom (a próxima é em dezembro/2026), ou ao menos antes da entrega do TCC, conferir esses números nas fontes oficiais e preencher "conteúdo revisado em" (`revisado_em`) no Admin, que aparece no artigo como "Atualizado em".

## Recuperar o acesso ao Admin local
**Sugestão:** https://www.notion.so/414d653a12cb81b1879af70e4f7dbd5f · **Registrado em:** 10/11/2026 · **Origem:** Manual

A senha do administrador local (`pagliarinimvp`) foi esquecida e o `python manage.py changepassword pagliarinimvp` não deu certo em 10/11/2026. Sem o Admin local não dá para publicar nem editar rascunhos pelo caminho normal (em 10/11/2026 as prévias foram geradas com `Client.force_login`, como contorno). Refazer o `changepassword` com o Claude guiando e ver em que passo trava.

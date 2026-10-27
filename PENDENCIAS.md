# Pendências de Portal FinQuant

Melhorias e correções previstas. Cada item tem uma linha no banco 💡 Sugestões do Centro de Comando. Executado → Implementada no banco e o item sai daqui.

## App estudo_caso
**Sugestão:** https://www.notion.so/3fdd653a12cb81309b80c037ccb7851c · **Registrado em:** 18/10/2026 · **Origem:** Planejada

Do `README.md` ("Próximos passos (fase 2)"): App `estudo_caso`: comparação de uma estratégia ativa de compra de ações brasileiras (análise técnica + fundamentalista) com renda fixa e investimento passivo, usando pandas/numpy/yfinance.

**Base (27/10/2026):** o app vai ser construído a partir do projeto `Script Analise Quantitativa` (pasta irmã, em `Desktop\Projeto Final ADS\`). A análise sai desse script e é levada para o portal; não se começa do zero.

## Exportar as avaliações para a análise de qualidade
**Sugestão:** https://www.notion.so/3fdd653a12cb8127af26d5cfba4f775b · **Registrado em:** 18/10/2026 · **Origem:** Planejada

Do `README.md` ("Próximos passos (fase 2)"): Exportação dos dados de `avaliacoes` (via `pandas`) para a análise de qualidade do projeto na entrega final do TCC.

**Sequência (27/10/2026):** as avaliações ainda não foram abertas ao público, então não há dados para exportar. Ordem: (1) terminar o portal, incluindo o `estudo_caso`; (2) enviar o portal para as pessoas avaliarem; (3) só depois exportar e analisar os dados de `avaliacoes`.

## Recuperação de senha por e-mail
**Sugestão:** https://www.notion.so/405d653a12cb8199b61fe43fcf85fab7 · **Registrado em:** 26/10/2026 · **Origem:** Manual

O cadastro pede e-mail desde 26/10/2026, mas não há tela de "esqueci a senha": produção usa o backend de e-mail do console (`MAILERS` em `config/settings.py`). Configurar um SMTP (credenciais no painel do Render) e ligar as views de reset de senha do Django.

**Código pronto (27/10/2026):** telas de "esqueci a senha" em `/contas/esqueci-a-senha/` e SMTP lido do ambiente (`EMAIL_HOST` e afins, veja `.env.example`). Falta: criar a senha de app do Gmail e preencher `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` e `DEFAULT_FROM_EMAIL` no painel do Render; depois, testar o envio em produção.

## Portal sem espera ao abrir (cold start do Render)
**Sugestão:** https://www.notion.so/406d653a12cb81f6a57cca57cff2d4a0 · **Registrado em:** 27/10/2026 · **Origem:** Manual

O Render gratuito desliga o serviço depois de 15 minutos sem acesso, e a primeira visita depois disso leva cerca de 1 minuto. Solução escolhida: criar uma rota leve `/saude/` que responde "ok" **sem consultar o banco** (se o ping lesse o banco, o Neon ficaria ligado o mês inteiro, cerca de 186 horas de computação, acima das ~100 do plano gratuito) e cadastrar um monitor externo gratuito (UptimeRobot ou cron-job.org) que acessa a rota a cada 10 minutos. É tudo determinístico, sem IA. O plano gratuito do Render (750 h/mês) cobre o serviço ligado 24 h. Se o portal continuar no ar depois do TCC, reavaliar o plano pago do Render (Starter, cerca de US$ 7/mês).

**Rota pronta (27/10/2026):** `/saude/` responde "ok" sem consultar o banco (há teste garantindo zero consultas). Falta: depois do deploy, cadastrar o monitor externo apontando para `https://portal-finquant.onrender.com/saude/` a cada 10 minutos.

## Apagar o Postgres antigo do Render
**Sugestão:** https://www.notion.so/405d653a12cb81e4809dcf0eab305c3e · **Registrado em:** 26/10/2026 · **Origem:** Manual

O banco `portal-finquant-db` do Render está sem uso desde a migração para o Neon (28/08/2026) e saiu do `render.yaml` em 26/10/2026. Apagar pelo painel do Render depois de confirmar que a `DATABASE_URL` do serviço aponta para o Neon.

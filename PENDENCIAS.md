# Pendências de Portal FinQuant

Melhorias e correções previstas. Cada item tem uma linha no banco 💡 Sugestões do Centro de Comando. Executado → Implementada no banco e o item sai daqui.

## Conferir a 1ª rodada completa do pré-cálculo das análises (14/11/2026)
**Sugestão:** https://www.notion.so/413d653a12cb814894aad42acd4e59bd · **Registrado em:** 09/11/2026 · **Origem:** Manual

O pré-cálculo de madrugada (02:00–05:00, `estudo_caso/execucao.py`) foi ligado em 09/11/2026, depois de um teste aprovado no Render. No sábado, 14/11/2026, o deploy da 01:00 traz preços novos e a rodada das 02:00 refaz as 136 análises (60 seleções automáticas + 76 ações sozinhas). Conferir: (1) abrir uma amostra de análises (devem abrir prontas, com a data nova); (2) o histórico do UptimeRobot entre 02:00 e 05:00, para garantir que o site não travou. Os logs do Render gratuito só guardam 1 hora; se houver travamento, o `estudo_caso/vigia.py` grava a pilha das threads no log.

## Exportar as avaliações para a análise de qualidade
**Sugestão:** https://www.notion.so/3fdd653a12cb8127af26d5cfba4f775b · **Registrado em:** 18/10/2026 · **Origem:** Planejada

Do `README.md` ("Próximos passos (fase 2)"): Exportação dos dados de `avaliacoes` (via `pandas`) para a análise de qualidade do projeto na entrega final do TCC.

**Sequência (27/10/2026):** as avaliações ainda não foram abertas ao público, então não há dados para exportar. Ordem: (1) terminar o portal, incluindo o `estudo_caso`; (2) enviar o portal para as pessoas avaliarem; (3) só depois exportar e analisar os dados de `avaliacoes`.

## Recuperação de senha por e-mail
**Sugestão:** https://www.notion.so/405d653a12cb8199b61fe43fcf85fab7 · **Registrado em:** 26/10/2026 · **Origem:** Manual

O cadastro pede e-mail desde 26/10/2026, mas não há tela de "esqueci a senha": produção usa o backend de e-mail do console (`MAILERS` em `config/settings.py`). Configurar um SMTP (credenciais no painel do Render) e ligar as views de reset de senha do Django.

**Código pronto (27/10/2026):** telas de "esqueci a senha" em `/contas/esqueci-a-senha/` e SMTP lido do ambiente (`EMAIL_HOST` e afins, veja `.env.example`). As variáveis do Gmail foram preenchidas no Render em 27/10/2026.

**Bloqueio (27/10/2026):** o envio falha com `OSError: [Errno 101] Network is unreachable` porque o plano gratuito do Render bloqueia a saída nas portas SMTP (25, 465 e 587) desde setembro de 2025 ([changelog do Render](https://render.com/changelog/free-web-services-will-no-longer-allow-outbound-traffic-to-smtp-ports)). Não é erro de código nem de credencial. A tela continua respondendo "confira o seu e-mail", e a falha só aparece no log do Render ("Failed to send password reset email"). Decisão de 27/10/2026: ficar sem envio por enquanto; quem esquecer a senha pede ao admin, que troca pelo `/admin/`. Para retomar, escolher entre (1) um serviço de e-mail por API HTTPS, como o Brevo (gratuito, 300 e-mails/dia, aceita o Gmail como remetente), com `django-anymail`, ou (2) o plano pago do Render (Starter, cerca de US$ 7/mês), que libera o SMTP sem mudar o código. Enquanto isso, a tela de "esqueci a senha" mostra um aviso para falar com o administrador; ao retomar, ligar `RECUPERACAO_SENHA_ATIVA=True` no Render.

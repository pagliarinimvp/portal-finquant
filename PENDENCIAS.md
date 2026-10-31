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

**Código pronto (27/10/2026):** telas de "esqueci a senha" em `/contas/esqueci-a-senha/` e SMTP lido do ambiente (`EMAIL_HOST` e afins, veja `.env.example`). As variáveis do Gmail foram preenchidas no Render em 27/10/2026.

**Bloqueio (27/10/2026):** o envio falha com `OSError: [Errno 101] Network is unreachable` porque o plano gratuito do Render bloqueia a saída nas portas SMTP (25, 465 e 587) desde setembro de 2025 ([changelog do Render](https://render.com/changelog/free-web-services-will-no-longer-allow-outbound-traffic-to-smtp-ports)). Não é erro de código nem de credencial. A tela continua respondendo "confira o seu e-mail", e a falha só aparece no log do Render ("Failed to send password reset email"). Decisão de 27/10/2026: ficar sem envio por enquanto; quem esquecer a senha pede ao admin, que troca pelo `/admin/`. Para retomar, escolher entre (1) um serviço de e-mail por API HTTPS, como o Brevo (gratuito, 300 e-mails/dia, aceita o Gmail como remetente), com `django-anymail`, ou (2) o plano pago do Render (Starter, cerca de US$ 7/mês), que libera o SMTP sem mudar o código. Enquanto isso, a tela de "esqueci a senha" mostra um aviso para falar com o administrador; ao retomar, ligar `RECUPERACAO_SENHA_ATIVA=True` no Render.

## Procedência e lacunas nos dados
**Sugestão:** https://www.notion.so/40ad653a12cb81c5baa1da65238fb42e · **Registrado em:** 31/10/2026 · **Origem:** Manual

Padrão do Mapa de Feminicídio (`Portfólio/docs/referencias/mapafeminicidio-josyscript-com.md`): cada série ou indicador mostra fonte, data da coleta e, se possível, o hash do arquivo baixado; "sem dado" nunca vira zero nem repete o último valor sem aviso; período parcial avisado ("até setembro"); dados oficiais (B3, CVM, BCB) e cálculos derivados (retorno, volatilidade) com rótulo próprio, sem somar bases diferentes; frase curta de método junto de cada número. Serve também para o capítulo de metodologia do TCC. Encaixa junto com o app `estudo_caso`.

## Ver tabela ao lado dos gráficos e estado da tela na URL
**Sugestão:** https://www.notion.so/40ad653a12cb81ea8647fb2a5dee5889 · **Registrado em:** 31/10/2026 · **Origem:** Manual

Botão "Ver tabela" em cada gráfico (acessibilidade e conferência) e ativo, período e indicador guardados na URL, para compartilhar uma análise. Referência: `Portfólio/docs/referencias/mapafeminicidio-josyscript-com.md`.

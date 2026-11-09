from allauth.socialaccount.adapter import DefaultSocialAccountAdapter, _build_apps_from_settings
from allauth.socialaccount.providers import registry


class AdaptadorSocial(DefaultSocialAccountAdapter):
    """Lê os provedores (Google, GitHub) só das configurações quando todos estão lá.

    O allauth consulta a tabela de provedores do banco a cada visita a Entrar e Cadastro (3 consultas), mesmo
    com os provedores vindo das variáveis de ambiente (`SOCIALACCOUNT_PROVIDERS`, em `config/settings.py`). Em
    produção cada consulta custa ~0,18 s (Render em Oregon, Neon em São Paulo; medido em 09/11/2026).
    Se faltar algum provedor nas configurações, volta ao comportamento padrão, que também lê o banco: assim um
    provedor cadastrado pelo /admin/ continua funcionando.
    """

    def list_apps(self, request, provider=None, client_id=None):
        da_config = _build_apps_from_settings(provider=provider, client_id=client_id)
        precisa = {provider} if provider else {p.id for p in registry.get_class_list()}
        if precisa <= set(da_config):
            return [app for apps in da_config.values() for app in apps]
        return super().list_apps(request, provider=provider, client_id=client_id)

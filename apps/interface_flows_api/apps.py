from django.apps import AppConfig


class InterfaceFlowsApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.interface_flows_api"

    def ready(self):
        import apps.interface_flows_api.signals

from crispy_forms.bootstrap import Accordion, AccordionGroup, PrependedText
from crispy_forms.layout import Div, Layout
from django import forms
from django.utils.safestring import mark_safe

from apps.forms.base import AppBaseForm
from apps.forms.field.common import SRVCommonDivField
from apps.models import ShinyInstance
from projects.models import Flavor

__all__ = ["ShinyForm"]


class ShinyForm(AppBaseForm):
    flavor = forms.ModelChoiceField(queryset=Flavor.objects.none(), required=False, empty_label=None)
    port = forms.IntegerField(min_value=3000, max_value=9999, required=True)
    image = forms.CharField(max_length=255, required=True)
    shiny_app_path = forms.CharField(max_length=255, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.initial_subdomain = self.instance.subdomain.subdomain

    def _setup_form_fields(self):
        # Handle Volume field
        super()._setup_form_fields()

    def _setup_form_helper(self):
        super()._setup_form_helper()
        body = Div(
            SRVCommonDivField("name", placeholder="Name your app"),
            SRVCommonDivField("description", rows="3", placeholder="Provide a detailed description of your app"),
            SRVCommonDivField("tags"),
            SRVCommonDivField(
                "subdomain", placeholder="Enter a subdomain or leave blank for a random one", spinner=True
            ),
            SRVCommonDivField("flavor"),
            SRVCommonDivField("access"),
            SRVCommonDivField(
                "note_on_linkonly_privacy",
                placeholder="Describe why you want to make the app accessible only via a link",
            ),
            SRVCommonDivField("source_code_url", placeholder="Provide a link to the public source code"),
            SRVCommonDivField("port", placeholder="3838"),
            SRVCommonDivField("image", placeholder="registry/repository/image:tag"),
            Accordion(
                AccordionGroup(
                    "Advanced settings",
                    PrependedText(
                        "shiny_app_path",
                        "/srv/shiny-server",
                    ),
                    active=False,
                ),
            ),
            css_class="card-body",
        )

        self.helper.layout = Layout(body, self.footer)

    def clean_shiny_app_path(self):
        cleaned_data = super().clean()
        shiny_app_path = cleaned_data.get("shiny_app_path", None)
        if shiny_app_path and not shiny_app_path.startswith("/"):
            self.add_error("shiny_app_path", "Path must start with a forward slash.")
        # Check that the path is ascii and has forwarded slash
        if shiny_app_path and not shiny_app_path.isascii():
            self.add_error("shiny_app_path", "Path must be ASCII.")

        return shiny_app_path

    def clean(self):
        cleaned_data = super().clean()
        access = cleaned_data.get("access", None)
        source_code_url = cleaned_data.get("source_code_url", None)

        if access == "public" and not source_code_url:
            self.add_error("source_code_url", "Source is required when access is public.")

        return cleaned_data

    class Meta:
        model = ShinyInstance
        fields = [
            "name",
            "description",
            "volume",
            "flavor",
            "access",
            "note_on_linkonly_privacy",
            "source_code_url",
            "port",
            "image",
            "tags",
            "shiny_app_path",
        ]
        labels = {
            "tags": "Keywords",
            "note_on_linkonly_privacy": "Reason for choosing the link only option",
            "shiny_app_path": "Custom subpath for Shiny app after /srv/shiny-server/",
        }

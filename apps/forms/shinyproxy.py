from crispy_forms.layout import Layout, Div, Field, HTML
from django import forms

from apps.forms.base import AppBaseForm
from apps.models import ShinyInstance
from projects.models import Flavor

__all__ = [
    "ShinyForm"
]


class ShinyForm(AppBaseForm):
    flavor = forms.ModelChoiceField(queryset=Flavor.objects.none(), widget=forms.RadioSelect, required=False)
    port = forms.IntegerField(min_value=3000, max_value=9999, required=True)
    image = forms.CharField(max_length=255, required=True)


    def _setup_form_fields(self):
        # Handle Volume field
        super()._setup_form_fields()

    def _setup_form_helper(self):
        super()._setup_form_helper()
        body = Div(
            Field("name", placeholder="Name your app"),
            Field("description", rows="3", placeholder="Provide a detailed description of your app"),
            Field("subdomain", placeholder="Enter a subdomain or leave blank for a random one"),
            Field("flavor"),
            Field("access"),
            Field("source_code_url", placeholder="Provide a link to the public source code"),
            Field("port", placeholder="3838"),
            Field("image", placeholder="registry/repository/image:tag"),
            Field("tags"),
            css_class="card-body")

        self.helper.layout = Layout(
            body,
            self.footer
        )

    def clean(self):
        cleaned_data = super().clean()
        access = cleaned_data.get('access', None)
        source_code_url = cleaned_data.get('source_code_url', None)

        if access == 'public' and not source_code_url:
            self.add_error('source_code_url', 'Source is required when access is public.')


        return cleaned_data

    class Meta:
        model = ShinyInstance
        fields = ["name","description", "volume", "flavor", "access", "source_code_url", "port", "image", "tags"]
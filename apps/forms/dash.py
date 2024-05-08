from crispy_forms.layout import Layout, Div, Field, HTML
from django import forms

from apps.forms.base import AppBaseForm
from apps.models import DashInstance
from projects.models import Flavor

__all__ = [
    "DashForm"
]


class DashForm(AppBaseForm):
    flavor = forms.ModelChoiceField(queryset=Flavor.objects.none(), widget=forms.RadioSelect, required=False)
    port = forms.IntegerField(min_value=1024, max_value=65535, required=True)
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
            Field("source_code_url", rows="3"),
            Field("port", placeholder="8000"),
            Field("image", placeholder="registry/repository/image:tag"),
            Field("tags"),
            css_class="card-body")

        self.helper.layout = Layout(
            body,
            self.footer
        )
    
    def clean(self):
        cleaned_data = super().clean()
        access = cleaned_data.get('access')
        source_code_url = cleaned_data.get('source_code_url')

        if access == 'public' and not source_code_url:
            self.add_error('source_code_url', 'Source is required when access is public.')

        return cleaned_data

    class Meta:
        model = DashInstance
        fields = ["name","description", "flavor", "access", "source_code_url", "port", "image", "tags"]
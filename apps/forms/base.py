import uuid
from typing import Any

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Button, Div, Submit
from django import forms
from django.core.validators import RegexValidator
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe

from apps.forms import CustomField
from apps.helpers import HELP_MESSAGE_MAP
from apps.models import BaseAppInstance, Subdomain, VolumeInstance
from projects.models import Flavor, Project

__all__ = ["BaseForm", "AppBaseForm"]


class BaseForm(forms.ModelForm):
    """The most generic form for apps running on serve. Current intended use is for VolumesK8S type apps"""

    subdomain = forms.CharField(
        required=False,
        min_length=3,
        max_length=30,
        validators=[
            RegexValidator(
                regex=r"^(?!.*--)(?!^-)(?!.*-$)[a-z0-9]([a-z0-9-]{3,30}[a-z0-9])?$",
                message="Subdomain must be 3-30 characters long, contain only lowercase letters, digits, hyphens, "
                "and cannot start or end with a hyphen",
            )
        ],
    )

    def __init__(self, *args, **kwargs):
        self.project_pk = kwargs.pop("project_pk", None)
        self.project = get_object_or_404(Project, pk=self.project_pk) if self.project_pk else None
        self.model_name = self._meta.model._meta.verbose_name.replace("Instance", "")

        super().__init__(*args, **kwargs)

        self._setup_form_fields()
        self._setup_form_helper()

    def _setup_form_fields(self):
        # Populate subdomain field with instance subdomain if it exists
        if self.instance and self.instance.pk:
            self.fields["subdomain"].initial = self.instance.subdomain.subdomain

        # Handle name
        self.fields["name"].initial = ""

    def _setup_form_helper(self):
        # Create a footer for submit form or cancel
        self.footer = Div(
            Button("cancel", "Cancel", css_class="btn-danger", onclick="window.history.back()"),
            Submit("submit", "Submit"),
            css_class="card-footer d-flex justify-content-between",
        )
        self.helper = FormHelper(self)
        self.helper.form_method = "post"

    def clean_subdomain(self):
        cleaned_data = super().clean()
        subdomain_input = cleaned_data.get("subdomain")
        return self.validate_subdomain(subdomain_input)

    def clean_source_code_url(self):
        cleaned_data = super().clean()
        access = cleaned_data.get("access")
        source_code_url = cleaned_data.get("source_code_url")

        if access == "public" and not source_code_url:
            self.add_error("source_code_url", "Source is required when access is public.")

        return source_code_url

    def clean_note_on_linkonly_privacy(self):
        cleaned_data = super().clean()

        access = cleaned_data.get("access", None)
        note_on_linkonly_privacy = cleaned_data.get("note_on_linkonly_privacy", None)

        if access == "link" and not note_on_linkonly_privacy:
            self.add_error(
                "note_on_linkonly_privacy", "Please, provide a reason for making the app accessible only via a link."
            )

        return note_on_linkonly_privacy

    def validate_subdomain(self, subdomain_input):
        # If user did not input subdomain, set it to our standard release name
        if not subdomain_input:
            subdomain = "r" + uuid.uuid4().hex[0:8]
            if Subdomain.objects.filter(subdomain=subdomain_input).exists():
                error_message = "Wow, you just won the lottery. Contact us for a free chocolate bar."
                raise forms.ValidationError(error_message)
            return subdomain

        # Check if the instance has an existing subdomain
        current_subdomain = getattr(self.instance, "subdomain", None)

        # Validate if the subdomain input matches the instance's current subdomain
        if current_subdomain and current_subdomain.subdomain == subdomain_input:
            return subdomain_input

        # Check if the subdomain adheres to helm rules
        regex_validator = RegexValidator(
            regex=r"^(?!.*--)(?!^-)(?!.*-$)[a-z0-9]([a-z0-9-]{3,30}[a-z0-9])?$",
            message="Subdomain must be 3-30 characters long, contain only lowercase letters, digits, hyphens, "
            "and cannot start or end with a hyphen",
        )
        try:
            regex_validator(subdomain_input)
        except forms.ValidationError as e:
            raise forms.ValidationError(f"{e.message}")

        # Check for subdomain availability
        if Subdomain.objects.filter(subdomain=subdomain_input).exists():
            error_message = "Subdomain already exists. Please choose another one."
            raise forms.ValidationError(error_message)

        return subdomain_input

    def get_common_field(self, field_name: str, **kwargs):
        """
        This function is very useful because it allows you to create a custom field,
        that has a question_mark with tooltip next to the label. So "Name (?)" will have a tooltip.
        The text in the tooltip is defined in HELP_MESSAGE_MAP.
        The CustomField class just inherits the crispy_forms.layout.Field class and adds the
        help_message attribute to it. The template then uses it to render the tooltip for all fields
        using this class.
        """

        spinner = kwargs.pop("spinner", False)

        template = "apps/custom_field.html"
        base_args = dict(
            css_class="form-control form-control-with-spinner" if spinner else "form-control",
            wrapper_class="mb-3",
            rows=3,
            help_message=HELP_MESSAGE_MAP.get(field_name, ""),
            spinner=spinner,
        )

        base_args.update(kwargs)
        field = CustomField(field_name, **base_args)
        field.set_template(template)
        return Div(field, css_class="form-input-with-spinner" if spinner else None)

    class Meta:
        # Specify model to be used
        model = BaseAppInstance
        fields = "__all__"


class AppBaseForm(BaseForm):
    """
    Generic form for apps that require some compute power,
    so you can treat this form as an actual base form for the most of the apps
    """

    volume = forms.ModelChoiceField(
        queryset=VolumeInstance.objects.none(), required=False, empty_label="None", initial=None
    )

    flavor = forms.ModelChoiceField(queryset=Flavor.objects.none(), required=True, empty_label=None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _setup_form_fields(self):
        super()._setup_form_fields()
        flavor_queryset = (
            Flavor.objects.filter(project__pk=self.project_pk) if self.project_pk else Flavor.objects.none()
        )
        # Handle Flavor field
        self.fields["flavor"].label = "Hardware"
        self.fields["flavor"].queryset = flavor_queryset
        self.fields["flavor"].initial = flavor_queryset.first()  # if flavor_queryset else None

        # Handle Access field
        self.fields["access"].label = "Permission"

        # Handle Volume field
        volume_queryset = (
            VolumeInstance.objects.filter(project__pk=self.project_pk)
            if self.project_pk
            else VolumeInstance.objects.none()
        )

        self.fields["volume"].queryset = volume_queryset
        self.fields["volume"].initial = volume_queryset
        self.fields["volume"].help_text = f"Select a volume to attach to your {self.model_name}."

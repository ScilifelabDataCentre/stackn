# Generated by Django 5.0.2 on 2024-05-13 12:16

import django.db.models.deletion
import tagulous.models.fields
import tagulous.models.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("apps", "0009_rstudioinstance_vscodeinstance"),
        ("projects", "0003_remove_environment_appenv_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="customappinstance",
            name="volume",
            field=models.ManyToManyField(blank=True, to="apps.volumeinstance"),
        ),
        migrations.AlterField(
            model_name="customappinstance",
            name="flavor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="%(class)s",
                to="projects.flavor",
            ),
        ),
        migrations.AlterField(
            model_name="dashinstance",
            name="flavor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="%(class)s",
                to="projects.flavor",
            ),
        ),
        migrations.AlterField(
            model_name="jupyterinstance",
            name="flavor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="%(class)s",
                to="projects.flavor",
            ),
        ),
        migrations.AlterField(
            model_name="netpolicyinstance",
            name="flavor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="%(class)s",
                to="projects.flavor",
            ),
        ),
        migrations.AlterField(
            model_name="rstudioinstance",
            name="flavor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="%(class)s",
                to="projects.flavor",
            ),
        ),
        migrations.AlterField(
            model_name="shinyinstance",
            name="flavor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="%(class)s",
                to="projects.flavor",
            ),
        ),
        migrations.AlterField(
            model_name="volumeinstance",
            name="flavor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="%(class)s",
                to="projects.flavor",
            ),
        ),
        migrations.AlterField(
            model_name="vscodeinstance",
            name="flavor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="%(class)s",
                to="projects.flavor",
            ),
        ),
        migrations.CreateModel(
            name="Tagulous_TissuumapsInstance_tags",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, unique=True)),
                ("slug", models.SlugField()),
                (
                    "count",
                    models.IntegerField(default=0, help_text="Internal counter of how many times this tag is in use"),
                ),
                (
                    "protected",
                    models.BooleanField(default=False, help_text="Will not be deleted when the count reaches 0"),
                ),
            ],
            options={
                "ordering": ("name",),
                "abstract": False,
                "unique_together": {("slug",)},
            },
            bases=(tagulous.models.models.BaseTagModel, models.Model),
        ),
        migrations.CreateModel(
            name="TissuumapsInstance",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("chart", models.CharField(max_length=512)),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("deleted_on", models.DateTimeField(blank=True, null=True)),
                ("info", models.JSONField(blank=True, null=True)),
                ("name", models.CharField(default="app_name", max_length=512)),
                ("k8s_values", models.JSONField(blank=True, null=True)),
                ("url", models.URLField(blank=True, null=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                ("note_on_linkonly_privacy", models.TextField(blank=True, default="", null=True)),
                ("source_code_url", models.URLField(blank=True, null=True)),
                ("description", models.TextField(blank=True, default="", null=True)),
                (
                    "access",
                    models.CharField(
                        choices=[
                            ("project", "Project"),
                            ("private", "Private"),
                            ("public", "Public"),
                            ("link", "Link"),
                        ],
                        default="private",
                        max_length=20,
                    ),
                ),
                (
                    "app",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(app_label)s_%(class)s_related",
                        to="apps.apps",
                    ),
                ),
                (
                    "app_status",
                    models.OneToOneField(
                        null=True,
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="%(class)s",
                        to="apps.appstatus",
                    ),
                ),
                (
                    "flavor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="%(class)s",
                        to="projects.flavor",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(class)s",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="%(class)s", to="projects.project"
                    ),
                ),
                (
                    "subdomain",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE, related_name="%(class)s", to="apps.subdomain"
                    ),
                ),
                (
                    "tags",
                    tagulous.models.fields.TagField(
                        _set_tag_meta=True,
                        blank=True,
                        help_text="Enter a comma-separated tag string",
                        to="apps.tagulous_tissuumapsinstance_tags",
                    ),
                ),
                ("volume", models.ManyToManyField(blank=True, to="apps.volumeinstance")),
            ],
            options={
                "verbose_name": "TissUUmaps Instance",
                "verbose_name_plural": "TissUUmaps Instances",
                "permissions": [("can_access_app", "Can access app service")],
            },
        ),
    ]

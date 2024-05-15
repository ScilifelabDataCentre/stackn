# Generated by Django 5.0.2 on 2024-05-15 09:21

import django.db.models.deletion
import django.db.models.manager
import tagulous.models.fields
import tagulous.models.models
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("projects", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ObjectType",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(blank=True, default="Model", max_length=100, null=True)),
                ("slug", models.CharField(blank=True, default="model", max_length=100, null=True)),
                ("app_slug", models.CharField(blank=True, max_length=100, null=True)),
                ("enabled", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="Metadata",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("run_id", models.CharField(max_length=32)),
                ("trained_model", models.CharField(default="", max_length=32)),
                ("project", models.CharField(default="", max_length=255)),
                ("model_details", models.TextField(blank=True)),
                ("parameters", models.TextField(blank=True)),
                ("metrics", models.TextField(blank=True)),
            ],
            options={
                "unique_together": {("run_id", "trained_model")},
            },
        ),
        migrations.CreateModel(
            name="ModelLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("run_id", models.CharField(max_length=32)),
                ("trained_model", models.CharField(default="", max_length=32)),
                ("project", models.CharField(default="", max_length=255)),
                ("training_started_at", models.CharField(max_length=255)),
                ("execution_time", models.CharField(default="", max_length=255)),
                ("code_version", models.CharField(default="", max_length=255)),
                ("current_git_repo", models.CharField(default="", max_length=255)),
                ("latest_git_commit", models.CharField(default="", max_length=255)),
                ("system_details", models.TextField(blank=True)),
                ("cpu_details", models.TextField(blank=True)),
                (
                    "training_status",
                    models.CharField(
                        choices=[("ST", "Started"), ("DO", "Done"), ("FA", "Failed")], default="ST", max_length=2
                    ),
                ),
            ],
            options={
                "unique_together": {("run_id", "trained_model")},
            },
        ),
        migrations.CreateModel(
            name="Tagulous_Model_tags",
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
            name="Model",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uid", models.CharField(max_length=255)),
                ("name", models.CharField(max_length=255)),
                ("version", models.CharField(default="1.0", max_length=255)),
                (
                    "release_type",
                    models.CharField(choices=[("M", "Major"), ("m", "Minor")], default="m", max_length=255),
                ),
                ("description", models.CharField(blank=True, max_length=255, null=True)),
                ("model_card", models.TextField(blank=True, null=True)),
                (
                    "access",
                    models.CharField(
                        choices=[("PR", "Private"), ("LI", "Limited"), ("PU", "Public")], default="PR", max_length=2
                    ),
                ),
                ("resource", models.URLField(blank=True, max_length=2048, null=True)),
                ("url", models.URLField(blank=True, max_length=512, null=True)),
                ("bucket", models.CharField(blank=True, default="models", max_length=200, null=True)),
                ("path", models.CharField(blank=True, default="models", max_length=200, null=True)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("CR", "Created"), ("DP", "Deployed"), ("AR", "Archived")], default="CR", max_length=2
                    ),
                ),
                (
                    "model_card_headline",
                    models.ImageField(blank=True, default=None, null=True, upload_to="models/image"),
                ),
                (
                    "docker_image",
                    models.OneToOneField(
                        blank=True,
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="projects.environment",
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="model_owner",
                        to="projects.project",
                    ),
                ),
                ("object_type", models.ManyToManyField(blank=True, to="models.objecttype")),
                (
                    "tags",
                    tagulous.models.fields.TagField(
                        _set_tag_meta=True,
                        blank=True,
                        help_text="Enter a comma-separated tag string",
                        to="models.tagulous_model_tags",
                    ),
                ),
            ],
            options={
                "unique_together": {("name", "version", "project")},
            },
            managers=[
                ("objects_version", django.db.models.manager.Manager()),
            ],
        ),
    ]

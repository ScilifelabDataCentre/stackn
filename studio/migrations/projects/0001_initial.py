# Generated by Django 5.0.2 on 2024-05-15 12:16

import django.db.models.deletion
import projects.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("apps", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Project",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("clone_url", models.CharField(blank=True, max_length=512, null=True)),
                ("description", models.TextField(blank=True, null=True)),
                ("name", models.CharField(max_length=512)),
                (
                    "apps_per_project",
                    models.JSONField(blank=True, default=projects.models.get_default_apps_per_project_limit, null=True),
                ),
                ("pattern", models.CharField(default="", max_length=255)),
                ("slug", models.CharField(max_length=512, unique=True)),
                ("status", models.CharField(blank=True, default="active", max_length=20, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("image", models.CharField(blank=True, max_length=2048, null=True)),
                ("project_key", models.CharField(max_length=512)),
                ("project_secret", models.CharField(max_length=512)),
                ("authorized", models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL)),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="owner",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "permissions": [("can_view_project", "Can view project")],
            },
        ),
        migrations.CreateModel(
            name="Flavor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("cpu_lim", models.TextField(blank=True, default="1000m", null=True)),
                ("gpu_lim", models.TextField(blank=True, default="0", null=True)),
                ("ephmem_lim", models.TextField(blank=True, default="200Mi", null=True)),
                ("mem_lim", models.TextField(blank=True, default="3Gi", null=True)),
                ("cpu_req", models.TextField(blank=True, default="200m", null=True)),
                ("gpu_req", models.TextField(blank=True, default="0", null=True)),
                ("ephmem_req", models.TextField(blank=True, default="200Mi", null=True)),
                ("mem_req", models.TextField(blank=True, default="0.5Gi", null=True)),
                ("name", models.CharField(max_length=512)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "project",
                    models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to="projects.project"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Environment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("image", models.CharField(max_length=100)),
                ("name", models.CharField(max_length=100)),
                ("repository", models.CharField(blank=True, max_length=100, null=True)),
                ("slug", models.CharField(blank=True, max_length=100, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("public", models.BooleanField(default=False)),
                ("app", models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to="apps.apps")),
                (
                    "project",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="projects.project"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="BasicAuth",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=512)),
                ("password", models.CharField(blank=True, default="", max_length=100)),
                ("username", models.CharField(blank=True, default="", max_length=100)),
                (
                    "owner",
                    models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL),
                ),
                (
                    "project",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ba_project",
                        to="projects.project",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ProjectLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("description", models.CharField(max_length=512)),
                ("headline", models.CharField(max_length=256)),
                (
                    "module",
                    models.CharField(
                        choices=[
                            ("DE", "deployments"),
                            ("LA", "labs"),
                            ("MO", "models"),
                            ("PR", "projects"),
                            ("RE", "reports"),
                            ("UN", "undefined"),
                        ],
                        default="UN",
                        max_length=2,
                    ),
                ),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="projects.project")),
            ],
        ),
        migrations.CreateModel(
            name="ProjectTemplate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("description", models.TextField(blank=True, null=True)),
                ("image", models.ImageField(blank=True, null=True, upload_to="projecttemplates/images/")),
                ("name", models.CharField(max_length=512)),
                ("revision", models.IntegerField(default=1)),
                ("slug", models.CharField(default="", max_length=512)),
                ("template", models.TextField(blank=True, null=True)),
                ("enabled", models.BooleanField(default=True)),
                ("available_apps", models.ManyToManyField(blank=True, related_name="available_apps", to="apps.apps")),
            ],
            options={
                "unique_together": {("slug", "revision")},
            },
        ),
        migrations.AddField(
            model_name="project",
            name="project_template",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.DO_NOTHING, to="projects.projecttemplate"
            ),
        ),
    ]

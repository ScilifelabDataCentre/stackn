# Generated by Django 5.0.2 on 2024-05-27 07:28

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("models", "0001_initial"),
        ("projects", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="NewsObject",
            fields=[
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("title", models.CharField(default="", max_length=60, primary_key=True, serialize=False)),
                ("body", models.TextField(blank=True, default="", max_length=2024, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Collection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("name", models.CharField(default="", max_length=200, unique=True)),
                ("description", models.TextField(blank=True, default="", max_length=1000)),
                ("website", models.URLField(blank=True)),
                ("logo", models.ImageField(blank=True, null=True, upload_to="collections/logos/")),
                ("slug", models.SlugField(blank=True, unique=True)),
                ("zenodo_community_id", models.CharField(blank=True, max_length=200, null=True)),
                (
                    "maintainer",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="collection_maintainer",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="PublicModelObject",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("obj", models.FileField(upload_to="models/objects/")),
                ("updated_on", models.DateTimeField(auto_now=True)),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("model", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to="models.model")),
            ],
        ),
        migrations.CreateModel(
            name="PublishedModel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=512)),
                ("pattern", models.CharField(default="", max_length=255)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                (
                    "collections",
                    models.ManyToManyField(blank=True, related_name="published_models", to="portal.collection"),
                ),
                ("model_obj", models.ManyToManyField(to="portal.publicmodelobject")),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="projects.project")),
            ],
        ),
    ]

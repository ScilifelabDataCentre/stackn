# Generated by Django 5.0.2 on 2024-05-03 12:14

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("apps", "0008_appstatusnew_subdomain_tagulous_jupyterinstance_tags_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="volumeinstance",
            name="size",
            field=models.IntegerField(
                default=1,
                help_text="Size in GB",
                validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)],
            ),
        ),
    ]
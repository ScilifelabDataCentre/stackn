# Generated by Django 4.1.7 on 2023-09-20 12:46

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("apps", "0012_alter_appinstance_tags_alter_apps_projects"),
    ]

    operations = [
        migrations.AddField(
            model_name="appinstance",
            name="description",
            field=models.TextField(blank=True, default="", null=True),
        ),
    ]
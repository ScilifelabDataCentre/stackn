# Generated by Django 5.0.2 on 2024-09-11 15:31

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="EventsObject",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("title", models.CharField(default="", max_length=200)),
                ("description", models.TextField(blank=True, default="", max_length=2024, null=True)),
                ("start_time", models.DateTimeField()),
                ("end_time", models.DateTimeField()),
                ("venue", models.CharField(default="", max_length=100)),
                ("speaker", models.CharField(default="", max_length=200)),
                ("registration_url", models.URLField()),
                ("recording_url", models.URLField(blank=True, null=True)),
            ],
        ),
    ]

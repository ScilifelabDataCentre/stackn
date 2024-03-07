# Generated by Django 4.2.7 on 2024-03-07 09:31

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0002_emailverificationtable"),
    ]

    operations = [
        migrations.CreateModel(
            name="FixtureVersion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("filename", models.CharField(max_length=255, unique=True)),
                ("hash", models.CharField(max_length=64)),
            ],
        ),
    ]

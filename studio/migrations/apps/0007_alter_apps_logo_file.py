# Generated by Django 3.2.11 on 2022-01-25 10:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0006_auto_20211213_1407'),
    ]

    operations = [
        migrations.AlterField(
            model_name='apps',
            name='logo_file',
            field=models.ImageField(blank=True, null=True, upload_to='apps/logos'),
        ),
    ]
# Generated by Django 2.2.13 on 2021-02-25 09:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '0004_auto_20201125_1543'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dataset',
            name='datasheet',
        ),
    ]
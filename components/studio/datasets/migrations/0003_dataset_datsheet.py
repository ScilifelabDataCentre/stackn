# Generated by Django 2.2.13 on 2020-11-25 15:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '0002_auto_20201029_1914'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataset',
            name='datsheet',
            field=models.FileField(default=None, upload_to='datasheets/'),
        ),
    ]

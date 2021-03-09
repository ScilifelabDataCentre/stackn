# Generated by Django 2.2.13 on 2021-02-16 21:21

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0021_auto_20210216_2121'),
    ]

    operations = [
        migrations.AlterField(
            model_name='apppermission',
            name='projects',
            field=models.ManyToManyField(to='projects.Project'),
        ),
        migrations.AlterField(
            model_name='apppermission',
            name='users',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL),
        ),
    ]
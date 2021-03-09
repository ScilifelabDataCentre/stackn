# Generated by Django 2.2.13 on 2021-02-09 12:43

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('deployments', '0005_auto_20201029_2008'),
        ('apps', '0003_appinstance'),
    ]

    operations = [
        migrations.AddField(
            model_name='appinstance',
            name='helmchart',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='deployments.HelmResource'),
        ),
        migrations.AddField(
            model_name='appinstance',
            name='info',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='appinstance',
            name='lab_session_owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='app_owner', to=settings.AUTH_USER_MODEL),
        ),
    ]
# Generated by Django 3.1.6 on 2021-02-24 12:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0007_auto_20210224_0759'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='s3storage',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='project_s3', to='projects.s3'),
        ),
    ]

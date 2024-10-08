# Generated by Django 5.1.1 on 2024-10-04 08:14

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0005_alter_flavor_cpu_lim_alter_flavor_ephmem_lim_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="flavor",
            name="cpu_lim",
            field=models.TextField(blank=True, default="2000m", null=True, verbose_name="CPU limit"),
        ),
        migrations.AlterField(
            model_name="flavor",
            name="cpu_req",
            field=models.TextField(blank=True, default="200m", null=True, verbose_name="CPU request"),
        ),
        migrations.AlterField(
            model_name="flavor",
            name="ephmem_lim",
            field=models.TextField(blank=True, default="1000Mi", null=True, verbose_name="Ephemeral storage limit"),
        ),
        migrations.AlterField(
            model_name="flavor",
            name="ephmem_req",
            field=models.TextField(blank=True, default="200Mi", null=True, verbose_name="Ephemeral storage request"),
        ),
        migrations.AlterField(
            model_name="flavor",
            name="mem_lim",
            field=models.TextField(blank=True, default="4Gi", null=True, verbose_name="Memory limit"),
        ),
        migrations.AlterField(
            model_name="flavor",
            name="mem_req",
            field=models.TextField(blank=True, default="0.5Gi", null=True, verbose_name="Memory request"),
        ),
        migrations.AlterField(
            model_name="flavor",
            name="name",
            field=models.CharField(max_length=512, verbose_name="Flavor name (N vCPU, N GB RAM)"),
        ),
    ]

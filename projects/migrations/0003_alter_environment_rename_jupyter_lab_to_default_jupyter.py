# Written manually by Nikita Churikov on 2024-09-11

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0002_alter_environment_app_alter_environment_image_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            """
            UPDATE projects_environment
            SET name = 'Default Jupyter Lab'
            WHERE name = 'Jupyter Lab'
            """
        )
    ]

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("algorithm", "0014_pathwayrun_filtered_words"),
    ]

    operations = [
        migrations.AddField(
            model_name="pathwayrun",
            name="passed_words",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=50),
                blank=True,
                null=True,
                size=None,
            ),
        ),
    ]

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("algorithm", "0003_query_label"),
    ]

    operations = [
        migrations.CreateModel(
            name="FunctionResult",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "words",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=30),
                        default=list,
                        size=None,
                    ),
                ),
                (
                    "answers",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=30),
                        default=list,
                        size=None,
                    ),
                ),
                (
                    "function",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="results",
                        to="algorithm.function",
                    ),
                ),
            ],
        ),
    ]

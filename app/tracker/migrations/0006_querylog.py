from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("algorithm", "0008_resultbatch_result"),
        ("tracker", "0005_migrate_temp_to_draft"),
    ]

    operations = [
        migrations.CreateModel(
            name="QueryLog",
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
                ("start", models.DateTimeField()),
                ("end", models.DateTimeField()),
                ("tokens_consumed", models.IntegerField()),
                (
                    "query",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="logs",
                        to="algorithm.query",
                    ),
                ),
            ],
        ),
    ]

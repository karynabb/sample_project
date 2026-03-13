from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("algorithm", "0022_resultbatch_visible"),
        ("tracker", "0007_delete_querylog"),
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
                ("input_word", models.CharField(max_length=50)),
                ("tokens_consumed", models.IntegerField(default=0)),
                ("start_time", models.DateTimeField()),
                ("end_time", models.DateTimeField()),
                (
                    "pathway",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="algorithm.pathway",
                    ),
                ),
            ],
        ),
    ]

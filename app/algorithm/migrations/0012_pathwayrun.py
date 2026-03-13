from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0015_alter_payment_questionnaire"),
        ("algorithm", "0011_lmmresult_queries_completed_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="PathwayRun",
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
                ("lmm_results", models.ManyToManyField(to="algorithm.lmmresult")),
                (
                    "pathway",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="algorithm.pathway",
                    ),
                ),
                (
                    "questionnaire",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="core.questionnaire",
                    ),
                ),
            ],
        ),
    ]

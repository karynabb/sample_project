from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("algorithm", "0015_pathwayrun_passed_words"),
    ]

    operations = [
        migrations.CreateModel(
            name="NegativeDataset",
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
                ("word", models.CharField(max_length=30, unique=True)),
            ],
        ),
    ]

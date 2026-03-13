from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("algorithm", "0012_pathwayrun"),
    ]

    operations = [
        migrations.CreateModel(
            name="ZipfsCache",
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
                ("word", models.CharField(max_length=50)),
                ("query_result", models.CharField(max_length=50)),
            ],
        ),
    ]

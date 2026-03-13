from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("algorithm", "0002_auto_20230213_0803"),
    ]

    operations = [
        migrations.AddField(
            model_name="query",
            name="label",
            field=models.CharField(
                blank=True,
                choices=[
                    ("dataset", "Dataset query"),
                    ("lmm", "LMM query"),
                    ("function", "Function query"),
                ],
                max_length=10,
                null=True,
            ),
        ),
    ]

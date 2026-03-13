from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("algorithm", "0021_alter_result_rationale_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="resultbatch",
            name="visible",
            field=models.BooleanField(default=False),
        ),
    ]

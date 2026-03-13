from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("algorithm", "0004_functionresult"),
    ]

    operations = [
        migrations.AddField(
            model_name="query",
            name="expected_answer",
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
    ]

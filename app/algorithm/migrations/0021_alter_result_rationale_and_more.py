from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0023_questionnaire_failed"),
        ("algorithm", "0020_delete_compoundword_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="result",
            name="rationale",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterUniqueTogether(
            name="namecandidate",
            unique_together={("name", "pathway", "questionnaire")},
        ),
    ]

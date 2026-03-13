from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0023_questionnaire_failed"),
        ("algorithm", "0022_resultbatch_visible"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="namecandidate",
            unique_together={("name", "questionnaire")},
        ),
    ]

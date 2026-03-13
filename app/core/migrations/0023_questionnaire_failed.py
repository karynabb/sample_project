from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0022_alter_questionnaire_user"),
    ]

    operations = [
        migrations.AddField(
            model_name="questionnaire",
            name="failed",
            field=models.BooleanField(default=False),
        ),
    ]

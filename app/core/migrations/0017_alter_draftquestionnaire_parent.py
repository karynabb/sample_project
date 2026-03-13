from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0016_draftquestionnaire_parent_questionnaire_parent"),
    ]

    operations = [
        migrations.AlterField(
            model_name="draftquestionnaire",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to="core.questionnaire",
            ),
        ),
    ]

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0015_alter_payment_questionnaire"),
    ]

    operations = [
        migrations.AddField(
            model_name="draftquestionnaire",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="core.questionnaire",
            ),
        ),
        migrations.AddField(
            model_name="questionnaire",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="core.questionnaire",
            ),
        ),
    ]

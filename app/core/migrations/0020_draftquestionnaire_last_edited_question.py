from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0019_alter_payment_payment_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="draftquestionnaire",
            name="last_edited_question",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]

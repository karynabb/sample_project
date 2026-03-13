from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0017_alter_draftquestionnaire_parent"),
    ]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="payment_type",
            field=models.CharField(
                choices=[("initial", "Initial"), ("buy_more", "Buy more")],
                default="initial",
                max_length=15,
            ),
        ),
    ]

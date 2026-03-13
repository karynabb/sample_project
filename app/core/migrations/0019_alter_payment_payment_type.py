from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0018_payment_payment_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="payment",
            name="payment_type",
            field=models.CharField(
                choices=[("initial", "Initial"), ("buy_more", "Buy more")],
                max_length=15,
            ),
        ),
    ]

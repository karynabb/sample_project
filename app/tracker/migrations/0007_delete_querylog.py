from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("tracker", "0006_querylog"),
    ]

    operations = [
        migrations.DeleteModel(
            name="QueryLog",
        ),
    ]

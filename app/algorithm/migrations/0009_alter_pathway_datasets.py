from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("algorithm", "0008_resultbatch_result"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pathway",
            name="datasets",
            field=models.ManyToManyField(
                blank=True, null=True, related_name="pathways", to="algorithm.dataset"
            ),
        ),
    ]

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("algorithm", "0009_alter_pathway_datasets"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pathwaylmm",
            name="pathway",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="lmms",
                to="algorithm.pathway",
            ),
        ),
    ]

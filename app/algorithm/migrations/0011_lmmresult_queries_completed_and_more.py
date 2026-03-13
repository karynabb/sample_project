from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("algorithm", "0010_alter_pathwaylmm_pathway"),
    ]

    operations = [
        migrations.AddField(
            model_name="lmmresult",
            name="queries_completed",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="lmmresult",
            name="queries_started",
            field=models.IntegerField(default=0),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tracker", "0007_delete_querylog"),
        ("algorithm", "0019_pathway_candidates_per_batch"),
    ]

    operations = [
        migrations.DeleteModel(
            name="CompoundWord",
        ),
        migrations.AlterUniqueTogether(
            name="datasetquery",
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name="datasetquery",
            name="dataset",
        ),
        migrations.RemoveField(
            model_name="datasetquery",
            name="query",
        ),
        migrations.DeleteModel(
            name="DoubleMeaning",
        ),
        migrations.RemoveField(
            model_name="function",
            name="queries",
        ),
        migrations.RemoveField(
            model_name="functionresult",
            name="function",
        ),
        migrations.RemoveField(
            model_name="lmm",
            name="queries",
        ),
        migrations.RemoveField(
            model_name="lmmresult",
            name="lmm",
        ),
        migrations.RemoveField(
            model_name="lmmresult",
            name="questionnaire",
        ),
        migrations.RemoveField(
            model_name="pathwaylmm",
            name="lmm",
        ),
        migrations.RemoveField(
            model_name="pathwaylmm",
            name="pathway",
        ),
        migrations.RemoveField(
            model_name="pathwayrun",
            name="lmm_results",
        ),
        migrations.RemoveField(
            model_name="pathwayrun",
            name="pathway",
        ),
        migrations.RemoveField(
            model_name="pathwayrun",
            name="questionnaire",
        ),
        migrations.DeleteModel(
            name="ZipfsCache",
        ),
        migrations.RemoveField(
            model_name="pathway",
            name="query",
        ),
        migrations.AlterField(
            model_name="pathway",
            name="datasets",
            field=models.ManyToManyField(
                blank=True, related_name="pathways", to="algorithm.dataset"
            ),
        ),
        migrations.DeleteModel(
            name="DatasetQuery",
        ),
        migrations.DeleteModel(
            name="Function",
        ),
        migrations.DeleteModel(
            name="FunctionResult",
        ),
        migrations.DeleteModel(
            name="LMM",
        ),
        migrations.DeleteModel(
            name="LMMResult",
        ),
        migrations.DeleteModel(
            name="PathwayLMM",
        ),
        migrations.DeleteModel(
            name="PathwayRun",
        ),
        migrations.DeleteModel(
            name="Query",
        ),
    ]

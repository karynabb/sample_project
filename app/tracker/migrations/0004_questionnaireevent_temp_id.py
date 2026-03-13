from django.db import migrations, models


def copy_draft_ids_to_temp_field(apps, schema_editor):
    QuestionnaireEvent = apps.get_model('tracker', "QuestionnaireEvent")
    for q_event in QuestionnaireEvent.objects.all():
        q_event.temp_id = q_event.draft.id
        q_event.save()


class Migration(migrations.Migration):
    dependencies = [
        ("tracker", "0003_auto_20230209_0917"),
    ]

    operations = [
        migrations.AddField(
            model_name="questionnaireevent",
            name="temp_id",
            field=models.IntegerField(default=0),
        ),
        migrations.RunPython(copy_draft_ids_to_temp_field)
    ]

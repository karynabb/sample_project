from django.db import migrations, models


def copy_temp_ids_to_draft_field(apps, schema_editor):
    QuestionnaireEvent = apps.get_model('tracker', "QuestionnaireEvent")
    for q_event in QuestionnaireEvent.objects.all():
        q_event.draft = q_event.temp_id
        q_event.save()


class Migration(migrations.Migration):
    dependencies = [
        ("tracker", "0004_questionnaireevent_temp_id"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="questionnaireevent",
            name="draft"
        ),
        migrations.AddField(
            model_name="questionnaireevent",
            name="draft",
            field=models.IntegerField(default=0),
        ),
        migrations.RunPython(copy_temp_ids_to_draft_field),
        migrations.RemoveField(
            model_name="questionnaireevent",
            name="temp_id",
        )
    ]

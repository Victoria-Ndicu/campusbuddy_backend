from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("study", "0004_remove_studygroup_campus_id_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="studyresource",
            name="uploader",
        ),
        migrations.AddField(
            model_name="studyresource",
            name="topic",
            field=models.CharField(
                blank=True,
                help_text="More specific topic within the subject",
                max_length=150,
            ),
        ),
        migrations.RunSQL(
            sql="SELECT 1;",
            reverse_sql="SELECT 1;",
        ),
        migrations.AlterField(
            model_name="studyresource",
            name="id",
            field=models.BigAutoField(
                auto_created=True,
                primary_key=True,
                serialize=False,
                verbose_name="ID",
            ),
        ),
    ]

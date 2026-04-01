from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ("study", "0001_initial"),  # replace "study" with your actual app name
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE tutors DROP COLUMN IF EXISTS campus_id;",
            reverse_sql="ALTER TABLE tutors ADD COLUMN campus_id VARCHAR(255) NULL;",
        ),
    ]
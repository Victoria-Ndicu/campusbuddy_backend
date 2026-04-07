"""
Migration: remove campus_id from Event, widen banner_url to TextField.

Run with:
    python manage.py migrate events
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        # Replace with your latest migration name
        ("events", "0001_initial"),
    ]

    operations = [
        # 1. Remove campus_id column and its index
        migrations.RemoveField(
            model_name="event",
            name="campus_id",
        ),

        # 2. Change banner_url from URLField(max_length=500) → TextField
        #    TextField has no max_length restriction, so base64 data URIs
        #    and long CDN URLs both fit without truncation.
        migrations.AlterField(
            model_name="event",
            name="banner_url",
            field=models.TextField(blank=True, null=True),
        ),
    ]
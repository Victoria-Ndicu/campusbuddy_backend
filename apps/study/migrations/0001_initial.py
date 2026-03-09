from django.conf import settings
from django.db import migrations, models
import uuid

class Migration(migrations.Migration):
    initial = True
    dependencies = [("authentication", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="Tutor",
            fields=[
                ("id",           models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("subjects",     models.JSONField(default=list)),
                ("hourly_rate",  models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("bio",          models.TextField(blank=True, null=True)),
                ("rating",       models.DecimalField(decimal_places=2, default=0.0, max_digits=3)),
                ("review_count", models.PositiveIntegerField(default=0)),
                ("available",    models.BooleanField(default=True)),
                ("campus_id",    models.CharField(max_length=80)),
                ("created_at",   models.DateTimeField(auto_now_add=True)),
                ("updated_at",   models.DateTimeField(auto_now=True)),
                ("user",         models.OneToOneField(on_delete=models.deletion.CASCADE, related_name="tutor_profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "tutors"},
        ),
        migrations.CreateModel(
            name="StudyBooking",
            fields=[
                ("id",           models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("subject",      models.CharField(max_length=100)),
                ("scheduled_at", models.DateTimeField()),
                ("duration_min", models.PositiveIntegerField(default=60)),
                ("status",       models.CharField(choices=[("pending","Pending"),("confirmed","Confirmed"),("cancelled","Cancelled"),("completed","Completed")], default="pending", max_length=20)),
                ("notes",        models.TextField(blank=True, null=True)),
                ("created_at",   models.DateTimeField(auto_now_add=True)),
                ("updated_at",   models.DateTimeField(auto_now=True)),
                ("student",      models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="study_bookings", to=settings.AUTH_USER_MODEL)),
                ("tutor",        models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="bookings", to="study.tutor")),
            ],
            options={"db_table": "study_bookings", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="StudyGroup",
            fields=[
                ("id",           models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name",         models.CharField(max_length=150)),
                ("subject",      models.CharField(max_length=100)),
                ("description",  models.TextField(blank=True, null=True)),
                ("max_members",  models.PositiveIntegerField(default=10)),
                ("member_count", models.PositiveIntegerField(default=1)),
                ("campus_id",    models.CharField(max_length=80)),
                ("active",       models.BooleanField(default=True)),
                ("created_at",   models.DateTimeField(auto_now_add=True)),
                ("creator",      models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="created_groups", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "study_groups", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="StudyGroupMember",
            fields=[
                ("id",        models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("joined_at", models.DateTimeField(auto_now_add=True)),
                ("group",     models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="memberships", to="study.studygroup")),
                ("user",      models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="study_groups_joined", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "study_group_members"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="StudyResource",
            fields=[
                ("id",             models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title",          models.CharField(max_length=200)),
                ("subject",        models.CharField(max_length=100)),
                ("resource_type",  models.CharField(choices=[("pdf","PDF"),("doc","Doc"),("video","Video"),("link","Link"),("other","Other")], max_length=30)),
                ("file_url",       models.URLField(max_length=500)),
                ("download_count", models.PositiveIntegerField(default=0)),
                ("campus_id",      models.CharField(max_length=80)),
                ("created_at",     models.DateTimeField(auto_now_add=True)),
                ("uploader",       models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="uploaded_resources", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "study_resources", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="StudyQuestion",
            fields=[
                ("id",           models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title",        models.CharField(max_length=300)),
                ("body",         models.TextField()),
                ("subject",      models.CharField(blank=True, max_length=100, null=True)),
                ("tags",         models.JSONField(blank=True, default=list)),
                ("answer_count", models.PositiveIntegerField(default=0)),
                ("upvotes",      models.PositiveIntegerField(default=0)),
                ("campus_id",    models.CharField(max_length=80)),
                ("created_at",   models.DateTimeField(auto_now_add=True)),
                ("updated_at",   models.DateTimeField(auto_now=True)),
                ("author",       models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="study_questions", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "study_questions", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="StudyAnswer",
            fields=[
                ("id",          models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("body",        models.TextField()),
                ("upvotes",     models.PositiveIntegerField(default=0)),
                ("is_accepted", models.BooleanField(default=False)),
                ("created_at",  models.DateTimeField(auto_now_add=True)),
                ("updated_at",  models.DateTimeField(auto_now=True)),
                ("author",      models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="study_answers", to=settings.AUTH_USER_MODEL)),
                ("question",    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="answers", to="study.studyquestion")),
            ],
            options={"db_table": "study_answers", "ordering": ["-is_accepted","-upvotes","created_at"]},
        ),
        migrations.AddConstraint(
            model_name="studygroupmember",
            constraint=models.UniqueConstraint(fields=["group","user"], name="unique_group_member"),
        ),
    ]

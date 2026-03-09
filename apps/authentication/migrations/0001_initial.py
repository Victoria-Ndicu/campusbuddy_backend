from django.db import migrations, models
import uuid

class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]
    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("password",        models.CharField(max_length=128, verbose_name="password")),
                ("last_login",       models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("id",               models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("email",            models.EmailField(db_index=True, max_length=254, unique=True)),
                ("phone",            models.CharField(blank=True, max_length=30, null=True)),
                ("role",             models.CharField(choices=[("student","Student"),("admin","Admin")], default="student", max_length=20)),
                ("is_verified",      models.BooleanField(default=False)),
                ("is_staff",         models.BooleanField(default=False)),
                ("is_active",        models.BooleanField(default=True)),
                ("is_superuser",     models.BooleanField(default=False)),
                ("full_name",        models.CharField(blank=True, max_length=120, null=True)),
                ("degree",           models.CharField(blank=True, max_length=120, null=True)),
                ("year_of_study",    models.SmallIntegerField(blank=True, null=True)),
                ("university",       models.CharField(blank=True, max_length=160, null=True)),
                ("avatar_url",       models.URLField(blank=True, max_length=500, null=True)),
                ("deleted_at",       models.DateTimeField(blank=True, null=True)),
                ("created_at",       models.DateTimeField(auto_now_add=True)),
                ("updated_at",       models.DateTimeField(auto_now=True)),
                ("groups",           models.ManyToManyField(blank=True, related_name="user_set", related_query_name="user", to="auth.group", verbose_name="groups")),
                ("user_permissions", models.ManyToManyField(blank=True, related_name="user_set", related_query_name="user", to="auth.permission", verbose_name="user permissions")),
            ],
            options={"db_table": "users", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="OtpCode",
            fields=[
                ("id",         models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("code",       models.CharField(max_length=255)),
                ("otp_type",   models.CharField(choices=[("email_verify","Email Verification"),("password_reset","Password Reset")], max_length=30)),
                ("expires_at", models.DateTimeField()),
                ("used",       models.BooleanField(default=False)),
                ("attempts",   models.SmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user",       models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="otp_codes", to="authentication.user")),
            ],
            options={"db_table": "otp_codes", "ordering": ["-created_at"]},
        ),
    ]

import uuid
from django.conf import settings
from django.db import models


class Tutor(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user         = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tutor_profile")
    subjects     = models.JSONField(default=list)
    hourly_rate  = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    bio          = models.TextField(blank=True, null=True)
    rating       = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    review_count = models.PositiveIntegerField(default=0)
    available    = models.BooleanField(default=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tutors"


class StudyBooking(models.Model):
    STATUS_CHOICES = [("pending","Pending"),("confirmed","Confirmed"),("cancelled","Cancelled"),("completed","Completed")]

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tutor        = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name="bookings")
    student      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="study_bookings")
    subject      = models.CharField(max_length=100)
    scheduled_at = models.DateTimeField()
    duration_min = models.PositiveIntegerField(default=60)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    notes        = models.TextField(blank=True, null=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "study_bookings"
        ordering = ["-created_at"]


class StudyGroup(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creator      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_groups")
    name         = models.CharField(max_length=150)
    subject      = models.CharField(max_length=100)
    description  = models.TextField(blank=True, null=True)
    max_members  = models.PositiveIntegerField(default=10)
    member_count = models.PositiveIntegerField(default=1)
    active       = models.BooleanField(default=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "study_groups"
        ordering = ["-created_at"]


class StudyGroupMember(models.Model):
    id        = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group     = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name="memberships")
    user      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="study_groups_joined")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = "study_group_members"
        unique_together = [["group", "user"]]


class StudyResource(models.Model):
    """
    Admin-managed only. Created and curated via the Django admin panel.
    Users can only list and view resources — no upload or edit access.
    """
    TYPE_CHOICES = [
        ("pdf",   "PDF"),
        ("doc",   "Doc"),
        ("video", "Video"),
        ("link",  "Link"),
        ("other", "Other"),
    ]

    # Auto-increment integer PK — no UUID needed for admin-managed content
    title         = models.CharField(max_length=200)
    subject       = models.CharField(max_length=100)
    topic         = models.CharField(max_length=150, blank=True, help_text="More specific topic within the subject")
    resource_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    file_url      = models.URLField(max_length=500)
    download_count = models.PositiveIntegerField(default=0)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "study_resources"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} [{self.subject}]"


class StudyQuestion(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="study_questions")
    title        = models.CharField(max_length=300)
    body         = models.TextField()
    subject      = models.CharField(max_length=100, blank=True, null=True)
    tags         = models.JSONField(default=list, blank=True)
    answer_count = models.PositiveIntegerField(default=0)
    upvotes      = models.PositiveIntegerField(default=0)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "study_questions"
        ordering = ["-created_at"]


class StudyAnswer(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question    = models.ForeignKey(StudyQuestion, on_delete=models.CASCADE, related_name="answers")
    author      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="study_answers")
    body        = models.TextField()
    upvotes     = models.PositiveIntegerField(default=0)
    is_accepted = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "study_answers"
        ordering = ["-is_accepted", "-upvotes", "created_at"]
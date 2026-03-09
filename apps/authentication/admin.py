from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import OtpCode, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ["email", "full_name", "role", "is_verified", "created_at"]
    list_filter   = ["role", "is_verified", "is_staff"]
    search_fields = ["email", "full_name", "phone"]
    ordering      = ["-created_at"]
    readonly_fields = ["created_at", "updated_at", "last_login"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("full_name", "phone", "degree", "year_of_study", "university", "avatar_url")}),
        ("Permissions", {"fields": ("role", "is_verified", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "created_at", "updated_at", "deleted_at")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2", "role")}),
    )


@admin.register(OtpCode)
class OtpCodeAdmin(admin.ModelAdmin):
    list_display  = ["user", "otp_type", "used", "attempts", "expires_at", "created_at"]
    list_filter   = ["otp_type", "used"]
    search_fields = ["user__email"]
    ordering      = ["-created_at"]
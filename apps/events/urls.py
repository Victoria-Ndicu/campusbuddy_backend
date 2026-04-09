"""EventBoard URL configuration."""
from django.urls import path
from . import views

app_name = "events"

urlpatterns = [
    # ── Collection ────────────────────────────────────────────────────
    # GET  → list published events (filters: category, search, from_date)
    # POST → create event  (body: CreateEventSerializer)
    path("", views.EventsView.as_view(), name="list"),

    # ── Single event ──────────────────────────────────────────────────
    # GET    → event detail + userRsvp field
    # PATCH  → update event (organiser / admin only)
    # DELETE → cancel event (organiser / admin only)
    path("<uuid:pk>/", views.EventDetailView.as_view(), name="detail"),

    # ── Banner upload ─────────────────────────────────────────────────
    # POST multipart/form-data { file } → { data: { bannerUrl } }
    path("uploads/banner/", views.EventBannerUploadView.as_view(), name="upload-banner"),

    # ── My RSVPs ──────────────────────────────────────────────────────
    # GET → paginated list of events the current user has RSVPed to
    # Optional: ?status=going|not_going|waitlist
    path("my-rsvps/", views.MyRSVPsView.as_view(), name="my-rsvps"),

#
    # ── RSVP ──────────────────────────────────────────────────────────
    # POST { status: "going" | "not_going" }
    path("<uuid:pk>/rsvp/", views.EventRSVPView.as_view(), name="rsvp"),

    # ── Reminders ─────────────────────────────────────────────────────
    # POST { event_id, remind_at }
    path("reminders/", views.EventReminderView.as_view(), name="reminder"),

    # ── Save / unsave ─────────────────────────────────────────────────
    # POST → toggles saved state, returns { saved: true|false }
    path("<uuid:pk>/save/", views.EventSaveView.as_view(), name="save"),

    # ── Broadcast ─────────────────────────────────────────────────────
    # POST { message } → push to all 'going' attendees (organiser only)
    path("<uuid:pk>/broadcast/", views.EventBroadcastView.as_view(), name="broadcast"),
]
from django.urls import path
from . import views

app_name = "study"

urlpatterns = [
    path("dashboard/",                                         views.DashboardView.as_view(),      name="dashboard"),
    # Tutors
    path("tutors/",                                            views.TutorsView.as_view(),         name="tutors"),
    path("tutors/<uuid:pk>/reviews/",                          views.TutorReviewsView.as_view(),   name="tutor-reviews"),
    # Bookings
    path("bookings/",                                          views.BookingsView.as_view(),       name="bookings"),
    path("bookings/<uuid:pk>/",                                views.BookingDetailView.as_view(),  name="booking-detail"),
    # Groups
    path("groups/",                                            views.GroupsView.as_view(),              name="groups"),
    path("groups/<uuid:pk>/",                                  views.GroupDetailView.as_view(),         name="group-detail"),
    path("groups/<uuid:pk>/join/",                             views.GroupJoinView.as_view(),           name="group-join"),
    path("groups/<uuid:pk>/leave/",                            views.GroupLeaveView.as_view(),          name="group-leave"),
    path("group-members/",                                     views.GroupMembersView.as_view()),
    # Sessions
    path("groups/<uuid:pk>/sessions/",                         views.GroupSessionsView.as_view(),       name="group-sessions"),
    path("groups/<uuid:pk>/sessions/<uuid:session_pk>/",       views.GroupSessionDetailView.as_view(),  name="group-session-detail"),
    # Messages
    path("groups/<uuid:pk>/messages/",                         views.GroupMessagesView.as_view(),       name="group-messages"),
 
    # Resources
    path("resources/",                                         views.ResourcesView.as_view(),      name="resources"),
    # Q&A
    path("questions/",                                         views.QuestionsView.as_view(),      name="questions"),
    path("questions/<uuid:pk>/",                               views.QuestionDetailView.as_view(), name="question-detail"),
    path("questions/<uuid:question_pk>/answers/",              views.AnswersView.as_view(),        name="answers"),
    path("questions/<uuid:pk>/upvote/",                        views.UpvoteQuestionView.as_view(), name="upvote"),
    path("questions/<uuid:question_pk>/answers/<uuid:answer_pk>/accept/", views.AcceptAnswerView.as_view(), name="accept-answer"),
]
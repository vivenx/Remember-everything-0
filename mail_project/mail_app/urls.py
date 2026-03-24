from django.urls import path
from . import views

urlpatterns = [
    path("send/", views.send_email, name="send_email"),
    path("", views.list_emails, name="list_emails"),
    path("<int:entry_id>/", views.email_detail, name="email_detail"),
    path("<int:entry_id>/move/", views.move_email, name="move_email"),
    path("<int:entry_id>/delete/", views.delete_email, name="delete_email"),
]
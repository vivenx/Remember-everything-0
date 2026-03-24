from django.contrib import admin
from .models import EmailMessage, MailBoxEntry


@admin.register(EmailMessage)
class EmailMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "sender", "recipient", "subject", "created_at")
    search_fields = ("subject", "body", "sender__username", "recipient__username")


@admin.register(MailBoxEntry)
class MailBoxEntryAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "message", "folder", "is_read", "moved_at")
    list_filter = ("folder", "is_read")
    search_fields = ("owner__username", "message__subject")
from django.conf import settings
from django.db import models


class Folder(models.TextChoices):
    INBOX = "inbox", "Inbox"
    SENT = "sent", "Sent"
    ARCHIVE = "archive", "Archive"
    TRASH = "trash", "Trash"


class EmailMessage(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_messages",
    )
    subject = models.CharField(max_length=255, blank=True, default="")
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.subject or "(Без темы)"


class MailBoxEntry(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mailbox_entries",
    )
    message = models.ForeignKey(
        EmailMessage,
        on_delete=models.CASCADE,
        related_name="entries",
    )
    folder = models.CharField(
        max_length=20,
        choices=Folder.choices,
        default=Folder.INBOX,
    )
    is_read = models.BooleanField(default=False)
    moved_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("owner", "message")
        ordering = ["-message__created_at"]

    def __str__(self):
        return f"{self.owner} -> {self.folder} -> {self.message_id}"
import json

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from .models import EmailMessage, MailBoxEntry, Folder

User = get_user_model()


def serialize_entry(entry):
    return {
        "entry_id": entry.id,
        "message_id": entry.message.id,
        "folder": entry.folder,
        "is_read": entry.is_read,
        "subject": entry.message.subject,
        "body": entry.message.body,
        "sender": {
            "id": entry.message.sender.id,
            "username": entry.message.sender.username,
        },
        "recipient": {
            "id": entry.message.recipient.id,
            "username": entry.message.recipient.username,
        },
        "created_at": entry.message.created_at.isoformat(),
    }


@csrf_exempt
@login_required
def send_email(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Некорректный JSON"}, status=400)

    recipient_id = data.get("recipient_id")
    subject = data.get("subject", "")
    body = data.get("body", "").strip()

    if not recipient_id or not body:
        return JsonResponse(
            {"error": "Поля recipient_id и body обязательны"},
            status=400,
        )

    if request.user.id == recipient_id:
        return JsonResponse(
            {"error": "Нельзя отправить письмо самому себе"},
            status=400,
        )

    recipient = get_object_or_404(User, id=recipient_id)

    with transaction.atomic():
        message = EmailMessage.objects.create(
            sender=request.user,
            recipient=recipient,
            subject=subject,
            body=body,
        )

        MailBoxEntry.objects.create(
            owner=request.user,
            message=message,
            folder=Folder.SENT,
            is_read=True,
        )

        MailBoxEntry.objects.create(
            owner=recipient,
            message=message,
            folder=Folder.INBOX,
            is_read=False,
        )

    return JsonResponse(
        {
            "message": "Письмо отправлено",
            "email_id": message.id,
        },
        status=201,
    )


@login_required
def list_emails(request):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    folder = request.GET.get("folder", Folder.INBOX)

    if folder not in Folder.values:
        return JsonResponse({"error": "Неизвестная папка"}, status=400)

    entries = (
        MailBoxEntry.objects
        .select_related("message", "message__sender", "message__recipient")
        .filter(owner=request.user, folder=folder)
        .order_by("-message__created_at")
    )

    return JsonResponse(
        {
            "folder": folder,
            "count": entries.count(),
            "emails": [serialize_entry(entry) for entry in entries],
        }
    )


@login_required
def email_detail(request, entry_id):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    entry = get_object_or_404(
        MailBoxEntry.objects.select_related(
            "message", "message__sender", "message__recipient"
        ),
        id=entry_id,
        owner=request.user,
    )

    if not entry.is_read and entry.folder != Folder.SENT:
        entry.is_read = True
        entry.save(update_fields=["is_read"])

    return JsonResponse(serialize_entry(entry))


@csrf_exempt
@login_required
def move_email(request, entry_id):
    if request.method not in ["PATCH", "POST"]:
        return HttpResponseNotAllowed(["PATCH", "POST"])

    entry = get_object_or_404(MailBoxEntry, id=entry_id, owner=request.user)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Некорректный JSON"}, status=400)

    target_folder = data.get("folder")

    if target_folder not in Folder.values:
        return JsonResponse({"error": "Неизвестная папка"}, status=400)

    entry.folder = target_folder
    entry.save(update_fields=["folder", "moved_at"])

    return JsonResponse(
        {
            "message": "Письмо перемещено",
            "entry_id": entry.id,
            "new_folder": entry.folder,
        }
    )


@csrf_exempt
@login_required
def delete_email(request, entry_id):
    if request.method != "DELETE":
        return HttpResponseNotAllowed(["DELETE"])

    entry = get_object_or_404(MailBoxEntry, id=entry_id, owner=request.user)
    message = entry.message

    entry.delete()

    if not message.entries.exists():
        message.delete()

    return JsonResponse({"message": "Письмо удалено"})
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import HttpResponse

from .models import Message
from tables.models import Table 

User = get_user_model()
MAX_MESSAGES_PER_PAGE = 12
MAX_CHARS_PER_MESSAGE = 255
SUPERUSER_USERNAME = "ElAmoDeLaMazmorra" # Nombre de usuario del superadministrador para recibir reportes

@login_required
def inbox(request):
    all_messages = Message.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).select_related('sender', 'recipient', 'related_table').order_by('-created_at')

    chats_data = {}
    total_unread_global = 0

    for msg in all_messages:
        if msg.sender == request.user:
            partner = msg.recipient
        else:
            partner = msg.sender
            
        partner_id = partner.id
        
        if partner_id not in chats_data:
            chats_data[partner_id] = {
                'sender': partner, 
                'last_message': msg,
                'unread_count': 0,
                'table_name': msg.related_table.name if msg.related_table else "General"
            }
        
        if msg.recipient == request.user and not msg.is_read:
            chats_data[partner_id]['unread_count'] += 1
            total_unread_global += 1

    chat_list = list(chats_data.values())
    chat_list.sort(key=lambda x: (x['unread_count'] > 0, x['last_message'].created_at), reverse=True)

    paginator = Paginator(chat_list, MAX_MESSAGES_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'messaging/inbox.html', {
        'chats': page_obj,
        'total_unread': total_unread_global
    })

@login_required
def chat_room(request, username):
    all_messages = Message.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).select_related('sender', 'recipient').order_by('-created_at')

    chats_data = {}
    for msg in all_messages:
        partner = msg.recipient if msg.sender == request.user else msg.sender
        
        if partner.id not in chats_data:
            chats_data[partner.id] = {
                'user': partner,
                'last_message': msg,
                'unread_count': 0
            }
        
        if msg.recipient == request.user and not msg.is_read:
            chats_data[partner.id]['unread_count'] += 1

    chat_list = list(chats_data.values())
    chat_list.sort(key=lambda x: x['last_message'].created_at, reverse=True)

    other_user = get_object_or_404(User, username=username)
    
    messages_in_chat = Message.objects.filter(
        Q(sender=request.user, recipient=other_user) | 
        Q(sender=other_user, recipient=request.user)
    ).order_by('created_at')

    Message.objects.filter(
        sender=other_user, 
        recipient=request.user, 
        read_at__isnull=True
    ).update(read_at=timezone.now())

    is_blocked = request.user.blocked_users.filter(pk=other_user.pk).exists()

    return render(request, 'messaging/chat_room.html', {
        'other_user': other_user,
        'chat_history': messages_in_chat,
        'chat_list': chat_list,
        'is_blocked': is_blocked,
    })

@login_required
def send_message(request):
    recipient_username = request.GET.get('to_user') or request.POST.get('to_user')
    table_id = request.GET.get('table_id') or request.POST.get('table_id')
    table_obj = None
    recipient = None

    if table_id:
        table_obj = get_object_or_404(Table, pk=table_id)

    if recipient_username:
        recipient = get_object_or_404(User, username=recipient_username)
    elif table_obj:
        recipient = table_obj.dm

    if recipient:
        if recipient.blocked_users.filter(pk=request.user.pk).exists():
            messages.error(request, "No puedes enviar mensajes a este usuario.")
            return redirect('chat_room', username=recipient.username)
        
        if request.user.blocked_users.filter(pk=recipient.pk).exists():
            messages.error(request, "Debes desbloquear a este usuario para enviarle mensajes.")
            return redirect('chat_room', username=recipient.username)

    if request.method == 'POST':
        subject = request.POST.get('subject') or "Mensaje de Chat"
        body = request.POST.get('body')
        
        if recipient and body:
            if len(body) > MAX_CHARS_PER_MESSAGE:
                messages.error(request, f"El mensaje es demasiado largo (máximo {MAX_CHARS_PER_MESSAGE} caracteres).")
                return redirect('chat_room', username=recipient.username)
            Message.objects.create(
                sender=request.user,
                recipient=recipient,
                subject=subject,
                body=body,
                related_table=table_obj
            )

            im_blocked = recipient.blocked_users.filter(pk=request.user.pk).exists()
            i_blocked = request.user.blocked_users.filter(pk=recipient.pk).exists()

            if not im_blocked and not i_blocked:
                MAX_MESSAGES = 50
                conversation = Message.objects.filter(
                    Q(sender=request.user, recipient=recipient) | 
                    Q(sender=recipient, recipient=request.user)
                ).order_by('-created_at')

                if conversation.count() > MAX_MESSAGES:
                    ids_to_delete = list(conversation[MAX_MESSAGES:].values_list('id', flat=True))                
                    if ids_to_delete:
                        Message.objects.filter(id__in=ids_to_delete).delete()

                if request.headers.get('HX-Request'):
                    messages_in_chat = Message.objects.filter(
                        Q(sender=request.user, recipient=recipient) | 
                        Q(sender=recipient, recipient=request.user)
                    ).order_by('created_at')
                    
                    return render(request, 'messaging/partials/message_list.html', {
                        'chat_history': messages_in_chat,
                        'request': request
                    })

            next_url = request.POST.get('next')
            if next_url:
                return redirect(next_url)
            
            if table_obj:
                return redirect('table_detail', pk=table_obj.id)
            
            return redirect('chat_room', username=recipient.username)

    return redirect('inbox')

@login_required
def mark_as_read(request, message_id):
    msg = get_object_or_404(Message, id=message_id, recipient=request.user)
    if not msg.read_at:
        msg.read_at = timezone.now()
        msg.save()
    return redirect('inbox')

@login_required
def get_chat_messages(request, username):
    # Esta vista es llamada cada 3 segundos por el chat
    other_user = get_object_or_404(User, username=username)
    
    messages = Message.objects.filter(
        Q(sender=request.user, recipient=other_user) | 
        Q(sender=other_user, recipient=request.user)
    ).order_by('created_at')

    Message.objects.filter(
        sender=other_user, 
        recipient=request.user, 
        read_at__isnull=True
    ).update(read_at=timezone.now())

    return render(request, 'messaging/partials/message_list.html', {
        'chat_history': messages,
        'request': request
    })

@login_required
def get_sidebar_chats(request):
    # Esta vista es llamada cada 10 segundos para actualizar la lista de la izquierda
    all_messages = Message.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).select_related('sender', 'recipient').order_by('-created_at')

    chats_data = {}
    
    for msg in all_messages:
        partner = msg.recipient if msg.sender == request.user else msg.sender
        
        if partner.id not in chats_data:
            chats_data[partner.id] = {
                'user': partner,
                'last_message': msg,
                'unread_count': 0
            }
        
        if msg.recipient == request.user and not msg.is_read:
            chats_data[partner.id]['unread_count'] += 1

    chat_list = list(chats_data.values())
    chat_list.sort(key=lambda x: x['last_message'].created_at, reverse=True)

    return render(request, 'messaging/partials/sidebar_list.html', {
        'chat_list': chat_list,
        'other_user_name': request.GET.get('active_chat') 
    })

@login_required
def block_user(request, username):
    user_to_block = get_object_or_404(User, username=username)
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
    
    if user_to_block.is_superuser or user_to_block.is_staff:
        messages.error(request, "No puedes bloquear a administradores o moderadores.")
        return redirect(next_url) if next_url else redirect('chat_room', username=username)

    if request.method == 'POST':
        request.user.blocked_users.add(user_to_block)
        messages.success(request, f"Has bloqueado a {user_to_block.username}.")
        
    return redirect(next_url) if next_url else redirect('chat_room', username=username)

@login_required
def unblock_user(request, username):
    user_to_unblock = get_object_or_404(User, username=username)    
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
    
    if request.method == 'POST':
        request.user.blocked_users.remove(user_to_unblock)
        messages.success(request, f"Has desbloqueado a {user_to_unblock.username}.")
        
    return redirect(next_url) if next_url else redirect('chat_room', username=username)

@login_required
def report_user(request, username):
    reported_user = get_object_or_404(User, username=username)    
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')

    if reported_user.is_superuser or reported_user.is_staff:
        messages.error(request, "No puedes reportar ni bloquear a administradores o moderadores.")
        return redirect(next_url) if next_url else redirect('chat_room', username=username)

    if request.method == 'POST':
        reason = request.POST.get('reason')
        should_block = request.POST.get('block_user') == 'on'
        
        try:
            admin_user = User.objects.get(username=SUPERUSER_USERNAME)
        except User.DoesNotExist:
            messages.error(request, "Error: No se encontró al administrador del sistema.")
            return redirect(next_url) if next_url else redirect('chat_room', username=username)

        last_messages = Message.objects.filter(
            Q(sender=request.user, recipient=reported_user) | 
            Q(sender=reported_user, recipient=request.user)
        ).order_by('-created_at')[:50]
        
        evidence_text = "\n\n--- ÚLTIMOS 50 MENSAJES ---\n"
        for msg in last_messages:
            evidence_text += f"[{msg.created_at.strftime('%Y-%m-%d %H:%M')}] {msg.sender}: {msg.body}\n"

        full_body = f"REPORTE DE USUARIO\nReportado por: {request.user.username}\nUsuario reportado: {reported_user.username}\n\nMotivo:\n{reason}\n{evidence_text}"

        Message.objects.create(
            sender=request.user,
            recipient=admin_user,
            subject=f"Reporte de usuario ({reported_user.username})",
            body=full_body
        )
        
        messages.success(request, "Reporte enviado a la administración.")

        if should_block:
            request.user.blocked_users.add(reported_user)
            messages.success(request, f"Has bloqueado a {reported_user.username}.")

    return redirect(next_url) if next_url else redirect('chat_room', username=username)

@login_required
def blocked_list(request):
    blocked_users = request.user.blocked_users.all()
    
    return render(request, 'messaging/blocked_list.html', {
        'blocked_users': blocked_users
    })

@login_required
def hx_unread_count(request):
    if not request.user.is_authenticated:
        return HttpResponse("")
    
    count = Message.objects.filter(recipient=request.user, read_at__isnull=True).count()
    
    if count > 0:
        return HttpResponse(str(count))
    else:
        return HttpResponse("")

@login_required
def support_ticket(request):
    if request.method == 'POST':
        subject = request.POST.get('subject', 'Soporte de usuario')
        body = request.POST.get('body', '')

        try:
            admin_user = User.objects.get(username=SUPERUSER_USERNAME)            
            Message.objects.create(
                sender=request.user,
                recipient=admin_user,
                subject=f"Soporte: {subject}",
                body=body
            )
            
            messages.success(request, "Tu reporte ha sido enviado. El equipo de soporte lo revisará pronto.")
            return redirect('chat_room', username=SUPERUSER_USERNAME)
            
        except User.DoesNotExist:
            messages.error(request, "El sistema de soporte no está disponible en este momento.")
            return redirect('home')

    return render(request, 'messaging/support.html')

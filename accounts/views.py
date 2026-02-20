import random
import time
from django.core.mail import send_mail
from django.http import JsonResponse
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import update_session_auth_hash
from django.conf import settings
from django.contrib.auth.models import User

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.contrib.auth.views import LoginView, LogoutView
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required

from .forms import CustomUserCreationForm
from tables.models import TableInvitation
from .models import User
from gamesystems.models import GameSystem

User = get_user_model()

class CustomLoginView(LoginView):
    template_name = "login.html"

class CustomLogoutView(LogoutView):
    pass

def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = CustomUserCreationForm()

    return render(request, "register.html", {"form": form})

#@login_required
def home(request):
    pending_invitations = []
    if request.user.is_authenticated:
        pending_invitations = TableInvitation.objects.filter(receiver=request.user)
    
    return render(request, 'home.html', {'pending_invitations': pending_invitations})

@login_required
def user_profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    is_owner = request.user == profile_user
    is_blocked = request.user.blocked_users.filter(pk=profile_user.pk).exists()
    i_am_blocked = profile_user.blocked_users.filter(pk=request.user.pk).exists()

    if request.method == 'POST' and is_owner:
        edit_type = request.POST.get('edit_type')
        try:
            match edit_type:
                case 'avatar':
                    avatar_val = request.POST.get('avatar')
                    if avatar_val:
                        profile_user.avatar = avatar_val
                        messages.success(request, "Avatar actualizado.")

                case 'bio':
                    profile_user.bio = request.POST.get('bio', '')
                    messages.success(request, "Biografía actualizada.")

                case 'email':
                    new_email = request.POST.get('email')
                    if new_email and new_email != profile_user.email:
                        if User.objects.filter(email=new_email).exclude(pk=profile_user.pk).exists():
                            messages.error(request, "Error: Ese correo electrónico ya está en uso por otro usuario.")
                            return redirect('user_profile', username=username)
                        else:
                            profile_user.email = new_email
                            messages.success(request, "Correo electrónico actualizado.")

                case 'phone_number':
                    profile_user.phone_number = request.POST.get('phone_number', '')
                    messages.success(request, "Teléfono actualizado.")

                case 'location':
                    profile_user.location = request.POST.get('location', '')
                    messages.success(request, "Ubicación actualizada.")

                case 'birth_date':
                    dob = request.POST.get('birth_date')
                    if dob:
                        profile_user.birth_date = dob
                        messages.success(request, "Fecha de nacimiento actualizada.")

                case 'gender':
                    profile_user.gender = request.POST.get('gender', '')
                    messages.success(request, "Género actualizado.")
                
                case 'experience_level':
                    profile_user.experience_level = request.POST.get('experience_level')
                    messages.success(request, "Nivel de experiencia actualizado.")

                case 'play_style':
                    profile_user.play_style = request.POST.get('play_style')
                    messages.success(request, "Estilo de juego actualizado.")

                case 'favorite_system':
                    system_id = request.POST.get('favorite_system')
                    if system_id:
                        system_obj = GameSystem.objects.filter(id=system_id).first()
                        if system_obj:
                            profile_user.favorite_system = system_obj
                            messages.success(request, "Sistema favorito actualizado.")

                case 'update_login_privacy':
                    profile_user.is_last_login_public = request.POST.get('is_last_login_public') == 'on'
                    profile_user.save()
                    success_message = "La privacidad de conexión"

            profile_user.save()
            return redirect('user_profile', username=username)

        except Exception as e:
            messages.error(request, f"Ocurrió un error al guardar: {e}")

    context = {
        'profile_user': profile_user,
        'is_owner': is_owner,
        'is_blocked': is_blocked,
        'i_am_blocked': i_am_blocked,
        'avatars': User.Avatar.values,
        'game_systems': GameSystem.objects.all().order_by('name'),
    }

    return render(request, 'profile.html', context)

@login_required
def toggle_privacy(request):
    if request.method == 'POST':
        field_name = request.POST.get('field')
        allowed_fields = [
            'is_email_public', 'is_phone_public', 'is_location_public', 
            'is_birth_date_public', 'is_gender_public', 'is_last_login_public'
        ]
        
        if field_name in allowed_fields:
            current_value = getattr(request.user, field_name)
            setattr(request.user, field_name, not current_value)
            request.user.save()
            messages.success(request, "Privacidad actualizada.")
        else:
            messages.error(request, "Campo no válido.")
            
        next_url = request.POST.get('next') or 'home'
        return redirect(next_url)

    return redirect('home')

@login_required
def send_otp_email(request):
    if request.method == 'POST':
        otp = str(random.randint(100000, 999999))
        
        request.session['pwd_reset_otp'] = otp
        request.session['pwd_reset_otp_expiry'] = time.time() + 300 
        
        try:
            send_mail(
                'Código de seguridad - Cambio de contraseña',
                f'Hola {request.user.username},\n\nTu código de verificación es: {otp}\n\nEste código caducará en 5 minutos.',
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
                fail_silently=False,
            )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
def verify_otp(request):
    if request.method == 'POST':
        code = request.POST.get('otp')
        saved_otp = request.session.get('pwd_reset_otp')
        expiry = request.session.get('pwd_reset_otp_expiry', 0)

        if time.time() > expiry:
            return JsonResponse({'success': False, 'error': 'El código ha caducado. Solicita uno nuevo.'})
        
        if code == saved_otp:
            request.session['pwd_reset_verified'] = True
            return JsonResponse({'success': True})
            
        return JsonResponse({'success': False, 'error': 'Código incorrecto.'})

@login_required
def set_new_password(request):
    if request.method == 'POST':
        if not request.session.get('pwd_reset_verified'):
            return JsonResponse({'success': False, 'error': 'No estás autorizado.'})
            
        pwd1 = request.POST.get('pwd1')
        pwd2 = request.POST.get('pwd2')

        if pwd1 != pwd2:
            return JsonResponse({'success': False, 'error': 'Las contraseñas no coinciden.'})
            
        try:
            validate_password(pwd1, request.user)
        except ValidationError as e:
            error_msgs = "<br>".join(e.messages)
            return JsonResponse({'success': False, 'error': error_msgs})
            
        request.user.set_password(pwd1)
        request.user.save()
        update_session_auth_hash(request, request.user)
        
        request.session.pop('pwd_reset_otp', None)
        request.session.pop('pwd_reset_otp_expiry', None)
        request.session.pop('pwd_reset_verified', None)

        return JsonResponse({'success': True})

@login_required
def send_current_email_otp(request):
    if request.method == 'POST':
        otp = str(random.randint(100000, 999999))
        request.session['old_email_otp'] = otp
        request.session['old_email_otp_expiry'] = time.time() + 300 
        
        try:
            send_mail(
                'Autoriza el cambio de correo',
                f'Hola {request.user.username},\n\nAlguien solicitó cambiar tu correo electrónico. Tu código de autorización es: {otp}\n\nSi no fuiste tú, ignora este mensaje.',
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
                fail_silently=False,
            )
            return JsonResponse({'success': True, 'email': request.user.email})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
def verify_current_email_otp(request):
    if request.method == 'POST':
        code = request.POST.get('otp')
        saved_otp = request.session.get('old_email_otp')
        expiry = request.session.get('old_email_otp_expiry', 0)

        if time.time() > expiry:
            return JsonResponse({'success': False, 'error': 'Código caducado.'})
        
        if code == saved_otp:
            request.session['authorized_to_change_email'] = True
            return JsonResponse({'success': True})
            
        return JsonResponse({'success': False, 'error': 'Código incorrecto.'})

@login_required
def send_new_email_otp(request):
    if request.method == 'POST':
        if not request.session.get('authorized_to_change_email'):
            return JsonResponse({'success': False, 'error': 'No tienes autorización. Verifica tu correo actual primero.'})
            
        new_email = request.POST.get('new_email').lower()
        if User.objects.filter(email=new_email).exists():
            return JsonResponse({'success': False, 'error': 'Este correo ya está en uso.'})
            
        otp = str(random.randint(100000, 999999))
        request.session['new_email_otp'] = otp
        request.session['pending_new_email'] = new_email
        request.session['new_email_otp_expiry'] = time.time() + 300 
        
        try:
            send_mail(
                'Verifica tu nuevo correo',
                f'Tu código para confirmar tu nuevo correo en Waypoint TTRPG es: {otp}',
                settings.DEFAULT_FROM_EMAIL,
                [new_email],
                fail_silently=False,
            )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

@login_required
def verify_and_save_new_email(request):
    if request.method == 'POST':
        code = request.POST.get('otp')
        saved_otp = request.session.get('new_email_otp')
        new_email = request.session.get('pending_new_email')
        expiry = request.session.get('new_email_otp_expiry', 0)

        if time.time() > expiry:
            return JsonResponse({'success': False, 'error': 'Código caducado.'})
        
        if code == saved_otp and new_email:
            request.user.email = new_email
            request.user.save()            
            keys = ['old_email_otp', 'old_email_otp_expiry', 'authorized_to_change_email', 'new_email_otp', 'pending_new_email', 'new_email_otp_expiry']
            for k in keys:
                request.session.pop(k, None)
                
            return JsonResponse({'success': True})
            
        return JsonResponse({'success': False, 'error': 'Código incorrecto.'})

def forgot_password_page(request):
    return render(request, 'forgot_password.html')

def send_reset_otp(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').lower()
        user = User.objects.filter(email=email).first()
        if not user:
            return JsonResponse({'success': False, 'error': 'No hay ninguna cuenta registrada con este correo.'})
            
        otp = str(random.randint(100000, 999999))
        request.session['reset_otp'] = otp
        request.session['reset_email'] = email
        request.session['reset_otp_expiry'] = time.time() + 300 
        
        try:
            send_mail(
                'Recuperación de Contraseña - Wayfinder',
                f'Hola {user.username},\n\nTu código para restablecer tu contraseña es: {otp}\n\nEste código caduca en 5 minutos. Si no solicitaste esto, ignora este correo.',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'Error al enviar el correo. Intenta más tarde.'})
            
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

def verify_reset_otp(request):
    if request.method == 'POST':
        code = request.POST.get('otp')
        saved_otp = request.session.get('reset_otp')
        expiry = request.session.get('reset_otp_expiry', 0)

        if time.time() > expiry:
            return JsonResponse({'success': False, 'error': 'El código ha caducado. Solicita uno nuevo.'})
        
        if code == saved_otp:
            request.session['reset_authorized'] = True
            return JsonResponse({'success': True})
            
        return JsonResponse({'success': False, 'error': 'Código incorrecto.'})

def save_new_password(request):
    if request.method == 'POST':
        if not request.session.get('reset_authorized'):
            return JsonResponse({'success': False, 'error': 'No tienes autorización. Vuelve a empezar.'})
            
        pwd1 = request.POST.get('pwd1')
        pwd2 = request.POST.get('pwd2')
        email = request.session.get('reset_email')
        
        if not pwd1 or not pwd2:
            return JsonResponse({'success': False, 'error': 'Por favor, llena ambos campos.'})
            
        if pwd1 != pwd2:
            return JsonResponse({'success': False, 'error': 'Las contraseñas no coinciden.'})
            
        user = User.objects.filter(email=email).first()
        if not user:
            return JsonResponse({'success': False, 'error': 'Usuario no encontrado.'})

        try:
            validate_password(pwd1, user)
        except ValidationError as e:
            error_msgs = "<br>".join(e.messages)
            return JsonResponse({'success': False, 'error': error_msgs})
            
        user.set_password(pwd1)
        user.save()
        
        keys = ['reset_otp', 'reset_email', 'reset_otp_expiry', 'reset_authorized']
        for k in keys:
            request.session.pop(k, None)
                
        return JsonResponse({'success': True})
            
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

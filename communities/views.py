from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import OuterRef, Subquery, Exists

from .models import Community
from .models import CommunityMember
from .models import Event
from .forms import CommunityForm
from .forms import EventForm
from tables.models import Table

MAX_COMMUNITIES_PER_PAGE = 12

@login_required
def my_communities(request):
    sort_by = request.GET.get('sort', 'default')    
    role_subquery = CommunityMember.objects.filter(
        community=OuterRef('pk'),
        user=request.user
    ).values('role')[:1]

    communities = Community.objects.filter(members=request.user).annotate(
        user_role=Subquery(role_subquery)
    )

    if sort_by == 'newest':
        communities = communities.order_by('-created_at')
    elif sort_by == 'oldest':
        communities = communities.order_by('created_at')
    elif sort_by == 'role':
        communities = communities.order_by('user_role', 'name')
    elif sort_by == 'dm_official':
        from django.db.models import Case, When, Value, IntegerField
        communities = communities.annotate(
            is_dm_rank=Case(
                When(user_role='dm_official', then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).order_by('-is_dm_rank', 'name')
    else:
        communities = communities.order_by('name')

    paginator = Paginator(communities, MAX_COMMUNITIES_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'communities/my_communities.html', {
        'communities': page_obj,
        'current_sort': sort_by,
    })

@login_required
def create_community(request):
    if request.method == 'POST':
        form = CommunityForm(request.POST)
        if form.is_valid():
            community = form.save()
            
            CommunityMember.objects.create(
                user=request.user,
                community=community,
                role='founder'
            )
            
            messages.success(request, f"¡La comunidad '{community.name}' ha sido creada!")
            return redirect('my_communities')
    else:
        form = CommunityForm()

    return render(request, 'communities/create_community.html', {
        'form': form,
        'is_edit': False
    })

@login_required
def community_detail(request, slug):
    community = get_object_or_404(Community, slug=slug)    
    member_record = community.get_member(request.user)    
    event_form = EventForm()

    return render(request, 'communities/community_detail.html', {
        'community': community,
        'user_member': member_record,
        'event_form': event_form,
    })

@login_required
def edit_community(request, slug):
    community = get_object_or_404(Community, slug=slug)
    member_record = CommunityMember.objects.filter(community=community, user=request.user).first()
    
    if not member_record or member_record.role not in ['founder', 'moderator']:
        messages.error(request, "No tienes la autoridad necesaria para editar la comunidad.")
        return redirect('community_detail', slug=community.slug)

    if request.method == 'POST':
        form = CommunityForm(request.POST, instance=community)
        if form.is_valid():
            form.save()
            messages.success(request, f"¡La comunidad '{community.name}' ha sido actualizada con éxito!")
            return redirect('community_detail', slug=community.slug)
    else:
        form = CommunityForm(instance=community)

    return render(request, 'communities/create_community.html', {
        'form': form,
        'is_edit': True,
        'community': community
    })


@login_required
@require_POST
def delete_community(request, slug):
    community = get_object_or_404(Community, slug=slug)    
    member_record = CommunityMember.objects.filter(community=community, user=request.user).first()
    
    if not member_record or member_record.role != 'founder':
        messages.error(request, "¡Alto! Solo el Fundador puede eliminar la comunidad.")
        return redirect('community_detail', slug=community.slug)
        
    community_name = community.name
    community.delete()
    
    messages.success(request, f"La comunidad '{community_name}' ha sido eliminada.")
    return redirect('my_communities')

@login_required
def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    community = event.community
    member = community.get_member(request.user)    
    is_staff = member and (member.role in ['founder', 'moderator'] or member.is_official_dm)
    is_admin = member and member.role in ['founder', 'moderator']

    tables = Table.objects.filter(event=event).select_related('dm', 'system').annotate(
        is_official_dm_annotated=Exists(
            CommunityMember.objects.filter(
                community=event.community,
                user=OuterRef('dm'),
                is_official_dm=True
            )
        )
    )

    return render(request, 'communities/event_detail.html', {
        'event': event,
        'community': community,
        'member': member,
        'is_staff': is_staff,
        'is_admin': is_admin,
        'tables': tables,
    })

@login_required
def add_event(request, slug):
    community = get_object_or_404(Community, slug=slug)
    member = community.get_member(request.user)
    
    if not member or member.role not in [CommunityMember.Role.FOUNDER, CommunityMember.Role.MODERATOR]:
        messages.error(request, "No tienes permiso para crear eventos.")
        return redirect('community_detail', slug=slug)

    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.community = community
            event.created_by = request.user
            event.save()
            messages.success(request, "¡Evento creado con éxito!")
    return redirect('community_detail', slug=slug)

@login_required
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    community = event.community    
    member = community.get_member(request.user)
    if not member or member.role not in ['founder', 'moderator']:
        messages.error(request, "No tienes permiso.")
        return redirect('community_detail', slug=community.slug)

    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, "Evento actualizado correctamente.")
        else:
            messages.error(request, "Error al actualizar.")
            
    return redirect('community_detail', slug=community.slug)

@login_required
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    slug = event.community.slug
    member = event.community.get_member(request.user)

    if member and member.role in [CommunityMember.Role.FOUNDER, CommunityMember.Role.MODERATOR]:
        event.delete()
        messages.success(request, "Evento eliminado.")
    else:
        messages.error(request, "No tienes permiso.")
    
    return redirect('community_detail', slug=slug)

@login_required
def join_community(request, slug):
    community = get_object_or_404(Community, slug=slug)
    member_record = community.get_member(request.user)

    if member_record:
        messages.info(request, "Ya eres miembro de esta comunidad.")
    else:
        CommunityMember.objects.create(
            user=request.user,
            community=community,
            role='member'
        )
        messages.success(request, f"¡Te has unido a '{community.name}'!")
    
    return redirect('community_detail', slug=slug)

@login_required
def leave_community(request, slug):
    community = get_object_or_404(Community, slug=slug)
    member_record = community.get_member(request.user)

    if not member_record:
        messages.info(request, "No eres miembro de esta comunidad.")
    elif member_record.role == 'founder':
        messages.error(request, "¡Alto! El Fundador no puede abandonar la comunidad. Considera transferir la propiedad o eliminar la comunidad.")
    else:
        member_record.delete()
        messages.success(request, f"Has abandonado '{community.name}'.")
    
    return redirect('community_detail', slug=slug)

@login_required
@require_POST
def manage_member(request, slug):
    community = get_object_or_404(Community, slug=slug)
    requester = community.get_member(request.user)

    if not requester or requester.role not in ['founder', 'moderator']:
        messages.error(request, "No tienes permiso para gestionar miembros.")
        return redirect('community_detail', slug=slug)

    username = request.POST.get('username')
    action = request.POST.get('action')

    User = get_user_model()
    try:
        target_user = User.objects.get(username=username)
        target_member = CommunityMember.objects.get(community=community, user=target_user)
    except (User.DoesNotExist, CommunityMember.DoesNotExist):
        messages.error(request, f"El usuario '{username}' no es miembro de esta comunidad.")
        return redirect('community_detail', slug=slug)

    if target_member.role == 'founder':
        messages.error(request, "Nadie puede modificar los rangos ni expulsar al Fundador.")
        return redirect('community_detail', slug=slug)

    if target_member == requester:
        messages.warning(request, "No puedes aplicar estas acciones sobre ti mismo desde este menú.")
        return redirect('community_detail', slug=slug)

    if action == 'grant_mod':
        if requester.role != 'founder':
            messages.error(request, "Solo el Fundador puede nombrar Moderadores.")
        else:
            target_member.role = 'moderator'
            target_member.save()
            messages.success(request, f"{target_user.username} ha sido promovido a Moderador.")

    elif action == 'revoke_mod':
        if requester.role != 'founder':
            messages.error(request, "Solo el Fundador puede degradar Moderadores.")
        else:
            target_member.role = 'member'
            target_member.save()
            messages.success(request, f"{target_user.username} ha vuelto a ser Miembro regular.")

    elif action == 'grant_dm':
        target_member.is_official_dm = True
        target_member.save()
        messages.success(request, f"{target_user.username} ha sido nombrado DM Oficial.")

    elif action == 'revoke_dm':
        target_member.is_official_dm = False
        target_member.save()
        messages.success(request, f"Se le ha revocado el rango de DM Oficial a {target_user.username}.")

    elif action == 'kick':
        if requester.role == 'moderator' and target_member.role == 'moderator':
            messages.error(request, "Un Moderador no puede expulsar a otro Moderador.")
        else:
            target_member.delete()
            messages.success(request, f"{target_user.username} ha sido expulsado de la comunidad.")

    return redirect('community_detail', slug=slug)

def find_community(request):
    communities_list = Community.objects.all().order_by('-created_at')    
    paginator = Paginator(communities_list, MAX_COMMUNITIES_PER_PAGE) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'communities/find_community.html', {
        'page_obj': page_obj,
    })
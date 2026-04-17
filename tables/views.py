from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.urls import reverse

from .forms import TableForm
from .models import Table, TableInvitation, CampaignLog, TableNote
from characters.models import Character
from gamesystems.models import GameSystem
from communities.models import Event

MAX_TABLES_PER_PAGE = 15
TABLE_MAX_PLAYERS = 8
LOG_MAX_ENTRIES_PER_PAGE = 20
SEARCH_PAGE_SIZE = 9

@login_required
def create_table(request):
    success = False
    community_id = request.GET.get('community_id')
    event_id = request.GET.get('event')
    event = None
    if event_id:
        event = get_object_or_404(Event, id=event_id)
        member = event.community.get_member(request.user)
        if not member or (member.role not in ['founder', 'moderator'] and not member.is_official_dm):
            messages.error(request, "No tienes el rango necesario en esta comunidad para crear mesas en este evento.")
            return redirect('community_detail', slug=event.community.slug)
    
    if request.method == 'POST':
        form = TableForm(request.POST)
        if form.is_valid():
            new_table = form.save(commit=False)
            new_table.dm = request.user
            new_table.max_players = TABLE_MAX_PLAYERS
            c_id = request.POST.get('community_id_hidden')
            if c_id:
                new_table.community_id = c_id
            if event:
                new_table.community = event.community
                new_table.event = event
            new_table.save()
            success = True
            form = TableForm()            
            # return redirect('table_detail', pk=new_table.pk)
    else:
        form = TableForm()

    return render(request, 'tables/create_table.html', {
        'form': form, 
        'event': event,
        'community_id': community_id,
        'success': success
    })

@login_required
def my_tables(request):
    sort_by = request.GET.get('sort', 'default')
    
    tables_query = Table.objects.filter(
        Q(dm=request.user) | Q(players=request.user)
    ).select_related('system', 'dm').distinct()

    sorting_options = {
        'system': 'system__name',
        'oldest': 'created_at',
        'newest': '-created_at',
    }

    criteria = sorting_options.get(sort_by, '-created_at')
    tables_query = tables_query.order_by(criteria)

    paginator = Paginator(tables_query, MAX_TABLES_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Procesar atributos visuales SOLO para las mesas de la pagina actual
    for table in page_obj:
        if table.system:
             table.color = table.system.primary_color
        else:
             table.color = '#95a5a6'             

    return render(request, 'tables/my_tables.html', {
        'tables': page_obj,
        'current_sort': sort_by
    })

@login_required
def table_detail(request, pk):
    table = get_object_or_404(
        Table.objects.select_related('system'), 
        pk=pk
    )

    is_dm = (request.user == table.dm)
    is_player = table.players.filter(id=request.user.id).exists()
    is_guest = not is_dm and not is_player

    if getattr(table, 'is_private', False) and is_guest:
        return render(request, 'tables/table_detail.html', {
            #'table': table,
            'access_denied': True,
        })

    is_full = False
    
    if is_guest:
        current_players = table.players.count()
        is_full = current_players >= getattr(table, 'max_players', TABLE_MAX_PLAYERS)

    if table.system:
        table_color = table.system.primary_color
        table_dmtitle = table.system.dm_title
        table_playerstitle = table.system.players_title
    else:
        table_color = '#3498db'
        table_dmtitle = 'Director de Juego'
        table_playerstitle = 'Jugadores'

    user_character = None
    if is_player:
        user_character = table.characters.filter(owner=request.user).first()

    available_characters = []
    if request.user.is_authenticated: 
        available_characters = Character.objects.filter(
            owner=request.user,       
            system=table.system       
        ).exclude(id__in=table.characters.all())

    if is_dm:
        logs_queryset = table.logs.select_related('target_character', 'author').all()
    else:
        logs_queryset = table.logs.filter(is_public=True).select_related('target_character', 'author')
    
    recent_logs = logs_queryset.order_by('-created_at')[:5]

    return render(request, 'tables/table_detail.html', {
        'table': table,
        'table_color': table_color,
        'table_dmtitle': table_dmtitle,
        'table_playerstitle': table_playerstitle,
        'max_players': TABLE_MAX_PLAYERS,        
        'available_characters': available_characters,
        'user_character': user_character,
        'is_dm': is_dm,
        'is_player': is_player,
        'is_guest': is_guest,     
        'is_full': is_full,       
        'logs': recent_logs,
        'access_denied': False,
    })

@login_required
@require_POST
def join_table_character(request, pk):
    table = get_object_or_404(Table, pk=pk)
    character_id = request.POST.get('character_id')
    
    if character_id:
        new_character = get_object_or_404(Character, pk=character_id, owner=request.user)        
        current_char = table.characters.filter(owner=request.user).first()
        if current_char:
            table.characters.remove(current_char)
            
        table.characters.add(new_character)
        
    return redirect('table_detail', pk=pk)

@login_required
@require_POST
def leave_table_character(request, pk):
    table = get_object_or_404(Table, pk=pk)
    character = table.characters.filter(owner=request.user).first()
    if character:
        table.characters.remove(character)
        
    return redirect('table_detail', pk=pk)

@login_required
@require_POST
def delete_table(request, pk):
    table = get_object_or_404(Table, pk=pk)
    can_delete = False

    if request.user == table.dm:
        can_delete = True
    
    elif table.community:
        if table.community.can_manage_events(request.user):
            can_delete = True

    if not can_delete:
        messages.error(request, "No tienes permisos para eliminar esta mesa.")
        return redirect('table_detail', pk=table.pk)

    table.delete()
    messages.success(request, "La mesa ha sido eliminada correctamente.")
    return redirect('my_tables')

@login_required
def edit_table(request, pk):
    table = get_object_or_404(Table, pk=pk)

    if request.user != table.dm:
        messages.error(request, "No tienes permiso para editar esta mesa. Solo el DM puede hacerlo.")
        return redirect('table_detail', pk=table.pk)

    if table.is_archived and 'is_archived' not in request.POST:
        messages.warning(request, "Esta mesa está congelada debido a que el evento terminó. Debes desarchivarla para editarla.")
    
    if request.method == 'POST':
        form = TableForm(request.POST, instance=table)
        if form.is_valid():
            form.save()
            messages.success(request, "Mesa actualizada correctamente.")
            return redirect('table_detail', pk=table.pk)
    else:
        form = TableForm(instance=table)
    
    return render(request, 'tables/create_table.html', {
        'form': form,
        'is_edit': True,
        'table': table
    })

User = get_user_model()

@login_required
@require_POST
def invite_player(request, pk):
    table = get_object_or_404(Table, pk=pk, dm=request.user)
    username = request.POST.get('username')    
    current_count = table.players.count() + table.invitations.count()
    
    if current_count >= TABLE_MAX_PLAYERS:
        messages.error(request, f"La mesa está llena ({TABLE_MAX_PLAYERS} jugadores máx, incluyendo pendientes).")
        return redirect('table_detail', pk=pk)
        
    try:
        user_to_invite = User.objects.get(username=username)
        if user_to_invite == request.user:
            messages.error(request, "No puedes invitarte a ti mismo.")
        elif user_to_invite in table.players.all():
            messages.error(request, "Este usuario ya es jugador de la mesa.")
        elif TableInvitation.objects.filter(table=table, receiver=user_to_invite).exists():
            messages.error(request, "Ya hay una invitación pendiente para este usuario.")
        else:
            TableInvitation.objects.create(table=table, receiver=user_to_invite)
            messages.success(request, f"Invitación enviada a {username}.")            
    except User.DoesNotExist:
        messages.error(request, "El usuario no existe.")

    return redirect('table_detail', pk=pk)

@login_required
@require_POST
def cancel_invitation(request, invitation_id):
    try:
        invitation = TableInvitation.objects.get(id=invitation_id, table__dm=request.user)
        table_pk = invitation.table.pk
        invitation.delete()
        messages.success(request, "Invitación cancelada correctamente.")
        return redirect('table_detail', pk=table_pk)
        
    except TableInvitation.DoesNotExist:
        messages.error(request, "Esta invitación ya no se puede cancelar porque el jugador ya la ha aceptado, rechazado, o no existe.")
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')        
        return redirect(next_url) if next_url else redirect('my_tables')

@login_required
@require_POST
def respond_invitation(request, invitation_id, response):
    try:
        invitation = TableInvitation.objects.get(id=invitation_id, receiver=request.user)
    except TableInvitation.DoesNotExist:
        messages.error(request, "Esta invitación ya no existe o fue cancelada por el DM.")
        return redirect('my_tables')

    table = invitation.table
    
    if response == 'accept':
        if table.players.count() >= TABLE_MAX_PLAYERS:
            messages.error(request, "La mesa se llenó antes de que aceptaras.")
        else:
            table.players.add(request.user)
            messages.success(request, f"¡Te has unido a {table.name}!")
            invitation.delete()
    elif response == 'reject':
        invitation.delete()
        messages.info(request, "Invitación rechazada.")
        return redirect('home')

    return redirect('my_tables')

@login_required
@require_POST
def remove_player(request, table_id, user_id):
    table = get_object_or_404(Table, pk=table_id, dm=request.user)
    player = get_object_or_404(User, pk=user_id)    
    player_character = table.characters.filter(owner=player).first()

    if player_character:
        table.characters.remove(player_character)
    
    table.players.remove(player)
    
    messages.success(request, f"Jugador {player.username} y su personaje han sido eliminados de la mesa.")
    return redirect('table_detail', pk=table.pk)

@login_required
@require_POST
def promote_player(request, table_id, user_id):
    table = get_object_or_404(Table, pk=table_id, dm=request.user)
    new_dm = get_object_or_404(User, pk=user_id)    
    
    if new_dm in table.players.all():
        old_dm = request.user
        new_dm_character = table.characters.filter(owner=new_dm).first()
        if new_dm_character:
            table.characters.remove(new_dm_character)
            
        table.dm = new_dm    
        table.players.remove(new_dm)
        table.players.add(old_dm)
        table.save()
        
        messages.success(request, f"Has cedido el puesto de GD a {new_dm.username}.")
        return redirect('table_detail', pk=table.pk)
    
    return redirect('table_detail', pk=table.pk)

@login_required
def leave_table(request, pk):
    table = get_object_or_404(Table, pk=pk)
    
    if request.method == 'POST':
        if request.user in table.players.all():            
            table.players.remove(request.user)            
            personajes_del_jugador = table.characters.filter(owner=request.user)
            if personajes_del_jugador.exists():
                for personaje in personajes_del_jugador:
                    table.characters.remove(personaje)
            messages.success(request, f"Has abandonado la mesa '{table.name}' correctamente.")
            
    return redirect('my_tables')

@login_required
@require_POST
def add_log_entry(request, pk):
    table = get_object_or_404(Table, pk=pk)
    
    if request.user != table.dm:
        return redirect('table_detail', pk=pk)

    entry_type = request.POST.get('entry_type')
    content = request.POST.get('content')
    character_id = request.POST.get('character_id')    
    is_public_check = request.POST.get('is_public') == 'on'
    final_is_public = is_public_check if entry_type == 'FREE' else True
    target_char = None
    if character_id:
        target_char = table.characters.filter(id=character_id).first()
    
    CampaignLog.objects.create(
        table=table,
        entry_type=entry_type,
        content=content,
        target_character=target_char,
        is_public=final_is_public,
        author=request.user
    )

    return redirect_after_log(request, pk)

@login_required
def campaign_log_view(request, pk):
    table = get_object_or_404(Table, pk=pk)
    
    if request.user != table.dm and request.user not in table.players.all():
         return redirect('home')

    if request.user == table.dm:
        logs = table.logs.select_related('target_character', 'author').all()
    else:
        logs = table.logs.filter(is_public=True).select_related('target_character', 'author')

    type_filter = request.GET.get('type')    
    if type_filter:
        if type_filter == 'FREE_DM':
            logs = logs.filter(entry_type='FREE', is_public=False)
        elif type_filter == 'FREE_PUBLIC':
            logs = logs.filter(entry_type='FREE', is_public=True)
        else:
            logs = logs.filter(entry_type=type_filter)

    char_filter = request.GET.get('character')
    if char_filter and char_filter != '' and char_filter != 'None':
        try:
            int(char_filter) 
            logs = logs.filter(target_character_id=char_filter)
        except ValueError:
            pass

    sort_order = request.GET.get('sort', 'desc')
    if sort_order == 'asc':
        logs = logs.order_by('created_at')
    else:
        logs = logs.order_by('-created_at')

    characters = table.characters.all()

    paginator = Paginator(logs, LOG_MAX_ENTRIES_PER_PAGE) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'tables/campaign_log.html', {
        'table': table,
        'table_color': table.system.primary_color if table.system else '#3498db',
        'logs': page_obj,
        'characters': characters,
        'is_dm': request.user == table.dm,
        'current_type': type_filter,
        'current_char': char_filter,
        'current_sort': sort_order
    })

@login_required
@require_POST
def edit_log_entry(request, log_id):
    log = get_object_or_404(CampaignLog, pk=log_id)
    
    if request.user != log.table.dm:
        return redirect('campaign_log', pk=log.table.id)

    log.entry_type = request.POST.get('entry_type')
    log.content = request.POST.get('content')
    char_id = request.POST.get('character_id')
    log.target_character_id = char_id if char_id else None
    log.is_public = request.POST.get('is_public') == 'on' if log.entry_type == 'FREE' else True
    log.save()

    return HttpResponseRedirect(
        reverse('campaign_log', kwargs={'pk': log.table.id}) + '#add-log-btn'
    )

@login_required
@require_POST
def delete_log_entry(request, log_id):
    log = get_object_or_404(CampaignLog, pk=log_id)
    table_id = log.table.id
    
    if request.user == log.table.dm:
        log.delete()
        
    return HttpResponseRedirect(
        reverse('campaign_log', kwargs={'pk': table_id}) + '#add-log-btn'
    )

@login_required
def find_table(request):
    tables = Table.objects.filter(is_private=False).exclude(dm=request.user).exclude(players=request.user).order_by('-created_at')
    system = request.GET.get('system')
    if system: tables = tables.filter(system__slug=system)
    level = request.GET.get('level')
    if level: tables = tables.filter(experience_level=level)
    style = request.GET.get('style')
    if style: tables = tables.filter(play_style=style)
    price = request.GET.get('price')
    if price: tables = tables.filter(price_type=price)
    modality = request.GET.get('modality')
    if modality: tables = tables.filter(modality=modality)
    frequency = request.GET.get('frequency')
    if frequency: tables = tables.filter(frequency=frequency)
    play_days = request.GET.get('play_days')
    if play_days: tables = tables.filter(play_days__icontains=play_days)
    location = request.GET.get('location')
    if location: tables = tables.filter(location__icontains=location)
    hide_full = request.GET.get('hide_full')
    if hide_full == 'on':
        from django.db.models import F, Count
        tables = tables.annotate(num_players=Count('players')).filter(num_players__lt=F('max_players'))

    paginator = Paginator(tables, SEARCH_PAGE_SIZE) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    search_params = query_params.urlencode()

    context = {
        'page_obj': page_obj,
        'search_params': search_params,
        'systems': GameSystem.objects.all(),
        'filters': request.GET,
        'modalities': Table.Modality.choices,
        'levels': Table.ExperienceLevel.choices,
        'styles': Table.PlayStyle.choices,
        'prices': Table.PriceType.choices,
        'frequencies': Table.Frequency.choices,
        'days_choices': ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    }
    return render(request, 'tables/find_table.html', context)

@login_required
@require_POST
def add_note(request, pk):
    table = get_object_or_404(Table, pk=pk)
    if not table.players.filter(id=request.user.id).exists():
        return redirect('table_detail', pk=pk)

    content = request.POST.get('content', '').strip()
    if content:
        TableNote.objects.create(
            table=table,
            author=request.user,
            content=content
        )

    return redirect_after_note(request, pk)

@login_required
def table_notes_view(request, pk):
    table = get_object_or_404(Table, pk=pk)
    is_dm = request.user == table.dm
    is_player = table.players.filter(id=request.user.id).exists()

    if not is_dm and not is_player:
        return redirect('home')

    notes = table.notes.select_related('author').order_by('-created_at')

    search_query = request.GET.get('q', '').strip()
    if search_query:
        notes = notes.filter(content__icontains=search_query)

    author_filter = request.GET.get('author', '').strip()
    if author_filter:
        notes = notes.filter(author__username=author_filter)

    sort_order = request.GET.get('sort', 'desc')
    if sort_order == 'asc':
        notes = notes.order_by('created_at')

    note_authors = table.notes.select_related('author')\
        .values_list('author__username', flat=True)\
        .distinct()\
        .order_by('author__username')        

    paginator = Paginator(notes, LOG_MAX_ENTRIES_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'tables/table_notes.html', {
        'table': table,
        'table_color': table.system.primary_color if table.system else '#3498db',
        'notes': page_obj,
        'is_dm': is_dm,
        'is_player': is_player,
        'search_query': search_query,
        'current_sort': sort_order,
        'author_filter': author_filter,
        'note_authors':  note_authors,
        'notes_total': table.notes.count(),
    })

@login_required
@require_POST
def edit_note(request, note_id):
    from .models import TableNote
    note = get_object_or_404(TableNote, pk=note_id)

    if request.user != note.author:
        return redirect('table_notes', pk=note.table.id)

    content = request.POST.get('content', '').strip()
    if content:
        note.content = content
        note.save()

    return HttpResponseRedirect(
        reverse('table_notes', kwargs={'pk': note.table.id}) + '#add-note-btn'
    )

@login_required
@require_POST
def delete_note(request, note_id):
    from .models import TableNote
    note = get_object_or_404(TableNote, pk=note_id)

    if request.user == note.author:
        table_id = note.table.id
        note.delete()
        return redirect('table_notes', pk=table_id)

    return HttpResponseRedirect(
        reverse('table_notes', kwargs={'pk': note.table.id}) + '#add-note-btn'
    )

def redirect_after_log(request, pk):
    next_url = request.POST.get('next', '')
    if next_url:
        return HttpResponseRedirect(next_url)
    return HttpResponseRedirect(
        reverse('table_detail', kwargs={'pk': pk}) + '#campaign-log'
    )

def redirect_after_note(request, pk):
    next_url = request.POST.get('next', '')
    if next_url:
        return HttpResponseRedirect(next_url)
    return HttpResponseRedirect(
        reverse('table_notes', kwargs={'pk': pk}) + '#add-note-btn'
    )

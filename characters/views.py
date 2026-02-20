from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from tables.models import CampaignLog
from .models.base import Character
from .forms.factory import create_character_form

from gamesystems.models import GameSystem 

@login_required
def create_character(request):
    system_slug = request.GET.get("system")
    
    form = None
    selected_system = None
    success = False 

    if system_slug:
        selected_system = get_object_or_404(GameSystem, slug=system_slug)
        schema_data = selected_system.schema_definition
        
        DynamicFormClass = create_character_form(schema_data)
        form = DynamicFormClass(request.POST or None)

    if request.method == "POST" and form:
        if form.is_valid():
            cleaned = form.cleaned_data
            char_name = cleaned.pop('character_name', f"Personaje de {request.user.username}")
            
            Character.objects.create(
                owner=request.user,
                name=char_name,
                system=selected_system,
                data=cleaned
            )
            success = True 
            # form = DynamicFormClass() 

    systems = GameSystem.objects.all()
    
    return render(request, "characters/create_character.html", {
        "systems": systems,
        "form": form,
        "selected_system": selected_system,
        "success": success
    })

@login_required
def my_characters(request):
    characters = Character.objects.filter(owner=request.user).order_by('-created_at')
    return render(request, "characters/my_characters.html", {
        "characters": characters
    })

@login_required
def character_sheet(request, pk):
    character = get_object_or_404(Character, pk=pk)
    schema = character.system.schema_definition
    character.color = schema.get('meta', {}).get('color', '#3498db')
    recent_logs = CampaignLog.objects.filter(target_character=character).order_by('-created_at')[:5]
    
    return render(request, "characters/character_sheet.html", {
        "character": character,
        "schema": schema,
        "character_color": character.color,
        "recent_logs": recent_logs,
    })

@login_required
def edit_character(request, pk):
    character = get_object_or_404(Character, pk=pk, owner=request.user)
    selected_system = character.system
    schema_data = selected_system.schema_definition
    
    DynamicFormClass = create_character_form(schema_data)
    
    initial_data = character.data.copy()
    initial_data['character_name'] = character.name

    if request.method == "POST":
        form = DynamicFormClass(request.POST, request.FILES or None)
        
        if form.is_valid():
            cleaned = form.cleaned_data
            new_name = cleaned.pop('character_name', character.name)
            character.name = new_name
            character.data = cleaned
            character.save()
            return redirect('character_sheet', pk=character.pk)
    else:
        form = DynamicFormClass(initial=initial_data)

    return render(request, "characters/create_character.html", {
        "form": form,
        "selected_system": selected_system, 
        "is_edit": True,
        "character": character,
        # 'systems': GameSystem.objects.all()
    })

@login_required
@require_POST
def delete_character(request, pk):
    character = get_object_or_404(Character, pk=pk, owner=request.user)
    character.delete()
    return redirect('my_characters')

@login_required
def character_full_log(request, char_id):
    character = get_object_or_404(Character, pk=char_id)
    logs_list = CampaignLog.objects.filter(target_character=character)
    log_type = request.GET.get('type')
    if log_type:
        logs_list = logs_list.filter(entry_type=log_type)

    sort_order = request.GET.get('sort', 'desc') 
    
    if sort_order == 'asc':
        logs_list = logs_list.order_by('created_at') 
    else:
        logs_list = logs_list.order_by('-created_at')

    paginator = Paginator(logs_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'character': character,
        'logs': page_obj,
        'current_type': log_type,
        'current_sort': sort_order, 
    }
    return render(request, 'characters/character_log.html', context)


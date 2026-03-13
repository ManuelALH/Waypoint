from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from tables.models import CampaignLog
from characters.models import Character
from characters.forms import create_character_form

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
    for char in characters:
        schema_meta = char.system.schema_definition.get("meta", {})
        card_fields = schema_meta.get("card_fields", [])

        char.display_stats = []

        for field in card_fields:
            key = field.get("key")
            icon = field.get("icon", "fa-info-circle")
            label = field.get("label", key.title())
            value = char.data.get(key)

            if value in [None, ""]:
                value = "-"

            char.display_stats.append({
                "icon": icon,
                "value": value,
                "label": label
            })

    return render(request, "characters/my_characters.html", {
        "characters": characters
    })

@login_required
def character_sheet(request, pk):
    character = get_object_or_404(Character, pk=pk)
    
    schema = character.system.schema_definition
    schema_meta = schema.get("meta", {})
    character_color = schema_meta.get("color", "#2c3e50")

    char_data = character.data
    display_fields = []

    for f_name, f_config in schema.items():
        if f_name in ["meta", "character_name"]: 
            continue
        
        field_type = f_config.get("type", "string")
        label = f_config.get("label", f_name.title())
        raw_value = char_data.get(f_name)

        if field_type == "skill_list":
            skills_to_display = []
            catalog = f_config.get("catalog", [])
            saved_skills = raw_value if isinstance(raw_value, dict) else {}
            
            for skill in catalog:
                s_id = skill.get("id")
                s_label = skill.get("label", s_id)
                s_data = saved_skills.get(s_id, {})
                
                skills_to_display.append({
                    "label": s_label,
                    "total": s_data.get("total", 0),
                    "prof": int(s_data.get("prof", 0))
                })
                
            display_fields.append({
                "type": "skill_list",
                "label": label,
                "skills": skills_to_display
            })
            
        elif field_type in ["choice", "select"]:
            choices = f_config.get("choices", [])
            display_value = raw_value
            for choice in choices:
                if choice[0] == raw_value:
                    display_value = choice[1]
                    break
                    
            display_fields.append({
                "type": "normal",
                "label": label,
                "value": display_value
            })
            
        else:
            display_fields.append({
                "type": "normal",
                "label": label,
                "value": raw_value if raw_value not in [None, ""] else "-"
            })

    return render(request, "characters/character_sheet.html", {
        "character": character,
        "character_color": character_color,
        "display_fields": display_fields,
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


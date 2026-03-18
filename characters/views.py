from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.urls import reverse

from tables.models import CampaignLog
from characters.models import Character
from characters.forms import create_character_form
from gamesystems.models import GameSystem 

MAX_ITEMS_SHOW = 10
MAX_ITEMS_PER_PAGE = 32
MAX_LOGS_SHOW = 5

@login_required
def create_character(request):
    system_slug = request.GET.get("system")
    form = None
    selected_system = None
    success = False 
    form_sections = []
    fields_placed = set()

    if system_slug:
        selected_system = get_object_or_404(GameSystem, slug=system_slug)
        schema_data = selected_system.schema_definition
        
        DynamicFormClass = create_character_form(schema_data)
        form = DynamicFormClass(request.POST or None)
        raw_sections = schema_data.get("meta", {}).get("sections", [])
        fields_placed = set()

        for section_def in raw_sections:
            section_form_fields = []
            for field_name in section_def.get("fields", []):
                is_hidden = schema_data.get(field_name, {}).get("hidden", False)
                if field_name in form.fields and field_name not in ('is_homebrew', 'custom_fields', 'character_name') and not is_hidden:
                    section_form_fields.append(form[field_name])
                    fields_placed.add(field_name)
            if section_form_fields:
                form_sections.append({
                    "label": section_def["label"],
                    "icon": section_def.get("icon", "fa-list"),
                    "fields": section_form_fields
                })

        # Campos sin sección asignada
        leftover = [
            form[name] for name in form.fields
            if name not in fields_placed and name not in ('is_homebrew', 'custom_fields', 'character_name') and not schema_data.get(name, {}).get("hidden", False)
        ]
        if leftover:
            form_sections.append({"label": "Others", "icon": "fa-ellipsis-h", "fields": leftover})

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
        "success": success,        
        "form_sections": form_sections,
        "section_field_names": fields_placed
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
    display_fields = {}
    hidden_fields = set()
    raw_inventory = character.inventory or []

    for f_name, f_config in schema.items():
        if f_name in ["meta", "character_name"]: 
            continue

        if f_config.get("hidden", False):
            hidden_fields.add(f_name)
            display_fields[f_name] = {
                "type": "normal",
                "label": f_config.get("label", f_name),
                "value": char_data.get(f_name, "-")
            }
        
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
                total = s_data.get("total", 0)
                
                skills_to_display.append({
                    "label": s_label,
                    "total": total,
                    "prof": int(s_data.get("prof", 0)),
                    "half":  total // 2,
                    "fifth": total // 5,
                })
                
            display_fields[f_name] = {
                "type": "skill_list",
                "label": label,
                "skills": skills_to_display,
                "has_thresholds": f_config.get("has_thresholds", False),
            }
            
        elif field_type in ["choice", "select"]:
            choices = f_config.get("choices", [])
            display_value = raw_value
            for choice in choices:
                if choice[0] == raw_value:
                    display_value = choice[1]
                    break
                    
            display_fields[f_name] = {
                "type": "normal",
                "label": label,
                "value": display_value or "-"
            }
            
        else:
            display_fields[f_name] = {
                "type": "normal",
                "label": label,
                "value": raw_value if raw_value not in [None, ""] else "-"
            }

    #Normalizar custom_fields al mismo formato display_fields
    custom_fields = char_data.get("custom_fields", [])
    display_custom = []
    if isinstance(custom_fields, list):
        for custom_field in custom_fields:
            if custom_field.get("type") == "homebrew_list":
                display_custom.append({
                    "type": "homebrew_list",
                    "label": custom_field.get("label"),
                    "items": custom_field.get("value", [])
                })
            else:
                display_custom.append({
                    "type": "normal",
                    "label": custom_field.get("label"),
                    "value": custom_field.get("value", "-")
                })

    schema_sections = schema_meta.get("sections", [])
    display_sections = []
    fields_already_placed = set(hidden_fields)

    for section_def in schema_sections:
        section_fields = []
        for field_name in section_def.get("fields", []):
            if field_name in display_fields:
                section_fields.append(display_fields[field_name])
                fields_already_placed.add(field_name)

        if section_fields:
            display_sections.append({
                "section": section_def["section"],
                "label": section_def["label"],
                "icon": section_def.get("icon", "fa-list"),
                "fields": section_fields
            })

    leftover_fields = [
        display_fields[name]
        for name in display_fields
        if name not in fields_already_placed
    ]
    if leftover_fields:
        display_sections.append({
            "sectionid": "other",
            "label": "Otros",
            "icon": "fa-ellipsis-h",
            "fields": leftover_fields
        })

    if display_custom:
        display_sections.append({
            "section": "custom",
            "label": "Atributos Personalizados",
            "icon": "fa-hammer",
            "fields": display_custom
        })

    sorted_inventory = sorted(
        raw_inventory,
        key=lambda item: 0 if item.get('favorite') else 1
    )

    recent_logs = CampaignLog.objects.filter(
        target_character=character
    ).order_by('-created_at')[:MAX_LOGS_SHOW]

    return render(request, "characters/character_sheet.html", {
        "character": character,
        "character_color": character_color,
        "display_sections": display_sections,
        "inventory": sorted_inventory[:MAX_ITEMS_SHOW],
        "inventory_total": len(sorted_inventory),
        "inventory_preview": True,
        "recent_logs": recent_logs
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

    raw_sections = schema_data.get("meta", {}).get("sections", [])
    form_sections = []
    fields_placed = set()

    for section_def in raw_sections:
        section_form_fields = []
        for field_name in section_def.get("fields", []):
            is_hidden = schema_data.get(field_name, {}).get("hidden", False)
            if field_name in form.fields and field_name not in ('is_homebrew', 'custom_fields', 'character_name') and not is_hidden:
                section_form_fields.append(form[field_name])
                fields_placed.add(field_name)
        if section_form_fields:
            form_sections.append({
                "label": section_def["label"],
                "icon": section_def.get("icon", "fa-list"),
                "fields": section_form_fields
            })

    leftover = [
        form[name] for name in form.fields
        if name not in fields_placed and name not in ('is_homebrew', 'custom_fields', 'character_name') and not schema_data.get(name, {}).get("hidden", False)
    ]
    if leftover:
        form_sections.append({"label": "Others", "icon": "fa-ellipsis-h", "fields": leftover})

    return render(request, "characters/create_character.html", {
        "form": form,
        "selected_system": selected_system, 
        "is_edit": True,
        "character": character,
        "form_sections": form_sections,
        "section_field_names": fields_placed
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

@login_required
@require_POST
def add_inventory(request, pk):
    character = get_object_or_404(Character, pk=pk, owner=request.user)
    name = request.POST.get('name', '').strip()
    quantity = request.POST.get('quantity', '1').strip()
    notes = request.POST.get('notes', '').strip()
    favorite = 'favorite' in request.POST
    
    if not name:
        return redirect('character_sheet', pk=pk)
    
    import time
    new_item = {
        "id": f"item_{int(time.time() * 1000)}",
        "name": name,
        "quantity": int(quantity) if quantity.isdigit() else 1,
        "notes": notes,
        "favorite": favorite
    }
    
    current_inventory = character.inventory or []
    current_inventory.append(new_item)
    character.inventory = current_inventory
    character.save()
    
    return redirect_to_inventory(request, pk)

@login_required
@require_POST
def edit_inventory(request, pk, item_id):
    character = get_object_or_404(Character, pk=pk, owner=request.user)    
    name = request.POST.get('name', '').strip()
    quantity = request.POST.get('quantity', '1').strip()
    notes = request.POST.get('notes', '').strip()
    favorite = 'favorite' in request.POST
    
    if not name:
        return redirect('character_sheet', pk=pk)
    
    updated_inventory = []
    for item in (character.inventory or []):
        if item.get('id') == item_id:
            updated_inventory.append({
                "id": item_id,
                "name": name,
                "quantity": int(quantity) if quantity.isdigit() else 1,
                "notes": notes,
                "favorite": favorite
            })
        else:
            updated_inventory.append(item)
    
    character.inventory = updated_inventory
    character.save()
    return redirect_to_inventory(request, pk)

@login_required
@require_POST
def delete_inventory(request, pk, item_id):
    character = get_object_or_404(Character, pk=pk, owner=request.user)
    
    character.inventory = [
        item for item in (character.inventory or [])
        if item.get('id') != item_id
    ]
    character.save()    
    return redirect_to_inventory(request, pk)

@login_required
@require_POST
def favorite_inventory(request, pk, item_id):
    character = get_object_or_404(Character, pk=pk, owner=request.user)    
    updated_inventory = []

    for item in (character.inventory or []):
        if item.get('id') == item_id:
            updated_inventory.append({
                **item,
                "favorite": not item.get('favorite', False)
            })
        else:
            updated_inventory.append(item)
    
    character.inventory = updated_inventory
    character.save()
    
    return redirect_to_inventory(request, pk)

@login_required
def character_inventory(request, pk):
    character = get_object_or_404(Character, pk=pk)
    raw_inventory = character.inventory or []
    search_query = request.GET.get('q', '').strip()
    if search_query:
        raw_inventory = [
            item for item in raw_inventory
            if search_query.lower() in item.get('name', '').lower()
        ]

    sorted_inventory = sorted(
        raw_inventory,
        key=lambda item: 0 if item.get('favorite') else 1
    )

    paginator = Paginator(sorted_inventory, MAX_ITEMS_PER_PAGE)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, "characters/character_inventory.html", {
        "character": character,
        "character_color": character.system.schema_definition.get("meta", {}).get("color", "#2c3e50"),
        "inventory": page_obj,
        "paginator": paginator,
        "search_query": search_query,
        "inventory_total": len(character.inventory or []),
    })

def redirect_to_inventory(request, pk):
    next_url = request.POST.get('next', '')
    if next_url:
        return HttpResponseRedirect(next_url)
    return HttpResponseRedirect(
        reverse('character_sheet', kwargs={'pk': pk}) + '#inventory'
    )

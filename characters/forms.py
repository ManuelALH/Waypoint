from django import forms
import json
import math
from .models import Character

def _dnd5e_ac_dex(arr):
    try:
        mod_dex = int(arr[0]) if len(arr) > 0 else 0
        dex_cap = int(arr[1]) if len(arr) > 1 else 99
    except (ValueError, TypeError):
        return 0
    if dex_cap == 0:
        return 0
    return min(mod_dex, dex_cap)

def _calc_pf1e_save(class_name, level, save_type):
    try:
        lvl = int(level or 0)
    except (ValueError, TypeError):
        lvl = 0

    save_table = {
        # --- Core Rulebook ---
        'barbarian':  {'fort': 'G', 'ref': 'P', 'will': 'P'},
        'bard':       {'fort': 'P', 'ref': 'G', 'will': 'G'},
        'cleric':     {'fort': 'G', 'ref': 'P', 'will': 'G'},
        'druid':      {'fort': 'G', 'ref': 'P', 'will': 'G'},
        'fighter':    {'fort': 'G', 'ref': 'P', 'will': 'P'},
        'monk':       {'fort': 'G', 'ref': 'G', 'will': 'G'},
        'paladin':    {'fort': 'G', 'ref': 'P', 'will': 'G'},
        'ranger':     {'fort': 'G', 'ref': 'G', 'will': 'P'},
        'rogue':      {'fort': 'P', 'ref': 'G', 'will': 'P'},
        'sorcerer':   {'fort': 'P', 'ref': 'P', 'will': 'G'},
        'wizard':     {'fort': 'P', 'ref': 'P', 'will': 'G'},
        # --- Advanced Player's Guide ---
        'alchemist':  {'fort': 'G', 'ref': 'G', 'will': 'P'},
        'cavalier':   {'fort': 'G', 'ref': 'P', 'will': 'P'},
        'inquisitor': {'fort': 'G', 'ref': 'P', 'will': 'G'},
        'oracle':     {'fort': 'P', 'ref': 'P', 'will': 'G'},
        'summoner':   {'fort': 'P', 'ref': 'P', 'will': 'G'},
        'witch':      {'fort': 'P', 'ref': 'P', 'will': 'G'},
        # --- Ultimate Combat / Ultimate Magic ---
        'gunslinger': {'fort': 'G', 'ref': 'G', 'will': 'P'},
        'magus':      {'fort': 'G', 'ref': 'P', 'will': 'P'},
        'vigilante':  {'fort': 'P', 'ref': 'G', 'will': 'G'},
        # --- Ultimate Wilderness ---
        'shifter':    {'fort': 'G', 'ref': 'G', 'will': 'P'},
        # --- Unchained ---
        'barbarian_unchained': {'fort': 'G', 'ref': 'P', 'will': 'P'},
        'monk_unchained':      {'fort': 'G', 'ref': 'G', 'will': 'G'},
        'rogue_unchained':     {'fort': 'P', 'ref': 'G', 'will': 'P'},
        'summoner_unchained':  {'fort': 'P', 'ref': 'P', 'will': 'G'},
        # --- Variantes ---
        'antipaladin': {'fort': 'G', 'ref': 'P', 'will': 'G'},
        'ninja':       {'fort': 'P', 'ref': 'G', 'will': 'P'},
        'samurai':     {'fort': 'G', 'ref': 'P', 'will': 'P'},
    }

    class_data = save_table.get(str(class_name), {})
    if not class_data:
        return 0

    progression = class_data.get(save_type, 'P')
    return (2 + math.floor(lvl / 2)) if progression == 'G' else math.floor(lvl / 3)

# Estas funciones son el espejo exacto del JS en create_character.html 
# Reciben: el valor original (val), todos los datos del formulario (data), y el mapa (mapping)
BACKEND_FORMULAS = {
    'map_value': lambda val, data, mapping: mapping.get(str(val), '') if mapping else '',
    'half_value': lambda val, data, mapping: math.floor(int(val or 0) / 2),
    'double_value': lambda val, data, mapping: math.floor(int(val or 0) * 2),
    'fifth_value': lambda val, data, mapping: math.floor(int(val or 0) / 5),
    'sum_values': lambda val, data, mapping: int(val or 0),
    'minus_values': lambda val, data, mapping, arr: max(0, (
        (int(arr[0]) if arr else 0) -
        sum(
            int(v) if isinstance(v, (int, float))
            else (int(v) if str(v).lstrip('-').isdigit() else 0)
            for v in arr[1:]
        )
    )),
    'misc_only': lambda val, data, mapping, arr: arr[-1] if arr else 0,
    'dnd5e_2014_mod': lambda val, data, mapping: math.floor((int(val or 0) - 10) / 2),
    'dnd5e_2014_pb': lambda val, data, mapping: math.ceil((int(val or 0) / 4) + 1),
    'dnd5e_ac_base': lambda val, data, mapping, arr: (10 if not arr or arr[0] in ('', 'unarmored') else 0),
    'dnd5e_ac_dex': lambda val, data, mapping, arr: _dnd5e_ac_dex(arr),
    'dnd5e_2014_skillcalc': lambda val, data, mapping, arr: (arr[0] if len(arr)>0 else 0) + ((arr[1] if len(arr)>1 else 0) * (arr[2] if len(arr)>2 else 0)),
    'pf1e_mod': lambda val, data, mapping: math.floor((int(val or 0) - 10) / 2),
    'pf1e_fort_base_save': lambda val, data, mapping, arr: _calc_pf1e_save(arr[0] if arr else '', arr[1] if len(arr) > 1 else 0, 'fort'),
    'pf1e_ref_base_save':  lambda val, data, mapping, arr: _calc_pf1e_save(arr[0] if arr else '', arr[1] if len(arr) > 1 else 0, 'ref'),
    'pf1e_will_base_save': lambda val, data, mapping, arr: _calc_pf1e_save(arr[0] if arr else '', arr[1] if len(arr) > 1 else 0, 'will'),
    'pf1e_cmstat': lambda val, data, mapping, arr: arr[1] if arr[0] == "Strength" else arr[2],
    'pf1e_cmd': lambda val, data, mapping, arr: sum(
        (v if isinstance(v, (int, float)) else (int(v) if str(v).lstrip('-').isdigit() else 0))
        for v in (arr[1:] if (arr[0] if arr else None) == "Strength" else arr[2:])
    ),
    'pf1e_skillcalc': lambda val, data, mapping, arr: (
        (arr[0] if len(arr) > 0 else 0) + 
        (3 if (len(arr) > 1 and arr[1] == 1) and (len(arr) > 2 and arr[2] > 0) else 0) + 
        (arr[2] if len(arr) > 2 else 0)
    ),
    'coc7e_hp': lambda val, data, mapping: math.floor(BACKEND_FORMULAS['sum_values'](val, data, mapping) / 10) if val>0 else 0,
    'coc7e_mp': lambda val, data, mapping: math.floor(int(val or 0) / 5) if val>0 else 0,
    'coc7e_mov': lambda val, data, mapping, arr: 7 if (arr[0]<arr[2] and arr[1]<arr[2]) else (9 if (arr[0]>arr[2] and arr[1]>arr[2]) else 8) if len(arr)>2 else 8,
    'coc7e_build': lambda val, data, mapping, arr: -2 if sum(arr[:2])<=64 else (-1 if sum(arr[:2])<=84 else (0 if sum(arr[:2])<=124 else (1 if sum(arr[:2])<=164 else 2))),
    'coc7e_db': lambda val, data, mapping, arr: "-2" if sum(arr[:2])<=64 else ("-1" if sum(arr[:2])<=84 else ("0" if sum(arr[:2])<=124 else ("+1D4" if sum(arr[:2])<=164 else "+1D6"))),
    'vtm5e_healthmax': lambda val, data, mapping: math.floor(int(val or 0) + 3),
    'gs_speed': lambda val, data, mapping: int(data.get('speed_roll', 0) or 0) * int(data.get('speed_bonus', 0) or 0),
    'gs_spelluses': lambda val, data, mapping: 0 if int(val or 0) <= 6 else (1 if int(val or 0) <= 9 else (2 if int(val or 0) <= 11 else 3)),
    'gs_fatigue_rank': lambda val, data, mapping: (
        0 if val <= 5  else
        1 if val <= 10 else
        2 if val <= 14 else
        3 if val <= 17 else
        4 if val <= 19 else
        5
    ),
    'dh_proficiency': lambda val, data, mapping: (
        1 if val <= 2  else
        2 if val <= 4 else
        3 if val <= 6 else
        4 if val <= 9 else
        5
    )
}

class CharacterForm(forms.ModelForm):
    class Meta:
        model = Character
        fields = "__all__"

def create_character_form(schema_data):    
    form_fields = {}

    form_fields['is_homebrew'] = forms.BooleanField(
        label="Modo Homebrew (Desactivar límites y fórmulas)",
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'homebrew-toggle form-check-input'})
    )

    form_fields['custom_fields'] = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'custom_homebrew_data'})
    )

    for field_name, field_config in schema_data.items():
        if field_name == "meta":
            continue

        if field_config.get("hidden", False):
            hidden_attrs = {'id': f'id_{field_name}', 'class': 'calculated-field'}
            if "source_fields" in field_config:
                source_ids = []
                for sf in field_config["source_fields"]:
                    if isinstance(sf, int):
                        source_ids.append(sf)
                    else:
                        source_ids.append(f"id_{sf}")
                hidden_attrs['data-source-ids'] = json.dumps(source_ids)
            elif "source_field" in field_config:
                hidden_attrs['data-source-ids'] = json.dumps([f"id_{field_config['source_field']}"])

            if "formula" in field_config:
                hidden_attrs['data-formula'] = field_config['formula']

            if "mapping" in field_config:
                hidden_attrs['data-mapping'] = json.dumps(field_config['mapping'])

            form_fields[field_name] = forms.CharField(
                required=False,
                widget=forms.HiddenInput(attrs=hidden_attrs)
            )
            continue

        widget_attrs = {}
        css_classes = "form-control"
        is_read_only = field_config.get("read_only", False)
        
        if is_read_only:
            widget_attrs['readonly'] = 'readonly'
            is_required = False 
            css_classes += " calculated-field"
            
            if "source_fields" in field_config:
                source_ids = []
                for sf in field_config["source_fields"]:
                    if isinstance(sf, int):
                        source_ids.append(sf)
                    else:
                        source_ids.append(f"id_{sf}")
                widget_attrs['data-source-ids'] = json.dumps(source_ids)
            elif "source_field" in field_config:
                widget_attrs['data-source-ids'] = json.dumps([f"id_{field_config['source_field']}"])                
            if "formula" in field_config:
                widget_attrs['data-formula'] = field_config['formula']
            if "mapping" in field_config:
                widget_attrs['data-mapping'] = json.dumps(field_config['mapping'])
        else:
            is_required = True

        if "range_mapping" in field_config:
            widget_attrs['data-range-mapping'] = json.dumps(field_config['range_mapping'])
            css_classes += " dynamic-range-field"
            if "source_fields" in field_config:
                widget_attrs['data-source-ids'] = json.dumps([f"id_{sf}" for sf in field_config['source_fields']])

        widget_attrs['class'] = css_classes        
        widget_attrs['placeholder'] = field_config.get("label", field_name.title())
        label = field_config.get("label", field_name.title())
        help_text = field_config.get("help_text", "")
        field_type = field_config.get("type", "string")
        default_value = field_config.get("default", None)

        if field_type == "int":
            int_kwargs = {
                'label': label,
                'required': is_required,
                'help_text': help_text,
                'initial': default_value,
            }
            
            if "min_value" in field_config and "range_mapping" not in field_config:
                #int_kwargs['min_value'] = field_config["min_value"]
                widget_attrs['min'] = field_config["min_value"]
                
            if "max_value" in field_config and "range_mapping" not in field_config:
                #int_kwargs['max_value'] = field_config["max_value"]
                widget_attrs['max'] = field_config["max_value"]
            
            if "min_field" in field_config:
                widget_attrs['data-min-field'] = field_config["min_field"]
                
            if "max_field" in field_config:
                widget_attrs['data-max-field'] = field_config["max_field"]                

            int_kwargs['widget'] = forms.NumberInput(attrs=widget_attrs)        
            form_fields[field_name] = forms.IntegerField(**int_kwargs)
        
        elif field_type in ["select", "choice"]:
            raw_choices = field_config.get("choices", [])
            choices = []
            if raw_choices:
                if not isinstance(raw_choices[0], (list, tuple)):
                    choices = [(c, c.title()) for c in raw_choices]
                else:
                    choices = raw_choices
            widget_attrs['data-is-choice'] = 'true'
            form_fields[field_name] = forms.CharField(
                label=label,  
                required=is_required,
                widget=forms.Select(choices=choices, attrs=widget_attrs), 
                help_text=help_text,
                initial=default_value          
            )

        elif field_type == "skill_list":
            widget_attrs['data-is-skill-list'] = 'true'
            widget_attrs['data-catalog'] = json.dumps(field_config.get("catalog", []))
            widget_attrs['data-formula'] = field_config.get("formula", "")
            widget_attrs['data-allow-custom'] = str(field_config.get("allow_custom", False)).lower()
            widget_attrs['data-has-misc'] = "true" if field_config.get("has_misc_bonus") else "false"
            widget_attrs['data-has-thresholds'] = "true" if field_config.get("has_thresholds") else "false"
            widget_attrs['data-filter-by'] = field_config.get("filter_by", "")
            
            form_fields[field_name] = forms.CharField(
                label=label,
                required=is_required,
                widget=forms.HiddenInput(attrs=widget_attrs),
                help_text=help_text,
                initial=default_value
            )

        elif field_type == "str_list":
            widget_attrs['data-is-str-list'] = 'true'
            widget_attrs['data-columns'] = json.dumps(
                field_config.get("columns_fields", [])
            )
            form_fields[field_name] = forms.CharField(
                label=label,
                required=False,
                widget=forms.HiddenInput(attrs=widget_attrs),
                help_text=help_text,
            )

        else:
            form_fields[field_name] = forms.CharField(
                label=label, required=is_required, 
                widget=forms.TextInput(attrs=widget_attrs), help_text=help_text,
                initial=default_value
            )

    def custom_clean(self):
        cleaned_data = super(self.__class__, self).clean()
        is_homebrew = cleaned_data.get('is_homebrew', False)

        custom_str = cleaned_data.get('custom_fields')
        if custom_str:
            try:
                cleaned_data['custom_fields'] = json.loads(custom_str)
            except json.JSONDecodeError:
                cleaned_data['custom_fields'] = []
        
        for f_name, f_config in schema_data.items():
            if f_name == "meta": continue

            if f_config.get("hidden", False):
                continue
            
            if f_config.get("read_only") and "formula" in f_config:
                if not is_homebrew:
                    formula_name = f_config["formula"]
                    mapping = f_config.get("mapping", {})
                    
                    if formula_name in BACKEND_FORMULAS:
                        total_val = 0
                        source_values_arr = []
                        
                        if "source_fields" in f_config:
                            for sf in f_config["source_fields"]:
                                if isinstance(sf, int):
                                    source_values_arr.append(sf)
                                    if isinstance(total_val, int):
                                        total_val += sf
                                else:
                                    val = cleaned_data.get(sf)
                                    if val is None:
                                        val = 0
                                    try:
                                        val_int = int(val)
                                        if isinstance(total_val, int):
                                            total_val += val_int
                                        source_values_arr.append(val_int)
                                    except (ValueError, TypeError):
                                        source_values_arr.append(val)                                    
                        elif "source_field" in f_config:
                            val = cleaned_data.get(f_config["source_field"])
                            if val is None: val = ""
                            try:
                                val_int = int(val)
                                total_val = val_int
                                source_values_arr.append(val_int)
                            except (ValueError, TypeError):
                                total_val = val
                                source_values_arr.append(val)
                            
                        try:
                            try:
                                real_value = BACKEND_FORMULAS[formula_name](total_val, cleaned_data, mapping, source_values_arr)
                            except TypeError:
                                real_value = BACKEND_FORMULAS[formula_name](total_val, cleaned_data, mapping)
                                
                            cleaned_data[f_name] = real_value
                        except Exception as e:
                            cleaned_data[f_name] = 0 if f_config.get("type") == "int" else ""                
                else:
                    pass

            if f_config.get("type") in ["select", "choice"]:
                val = cleaned_data.get(f_name)
                if not is_homebrew and val:
                    raw_choices = f_config.get("choices", [])
                    valid_keys = []
                    if raw_choices:
                        if not isinstance(raw_choices[0], (list, tuple)):
                            valid_keys = [str(c) for c in raw_choices]
                        else:
                            valid_keys = [str(c[0]) for c in raw_choices]
                    
                    if str(val) not in valid_keys:
                        self.add_error(f_name, f"La opción '{val}' no es válida. Activa el Modo Homebrew para valores personalizados.")
            
            if f_config.get("type") == "str_list":
                raw_val = cleaned_data.get(f_name, '')
                if raw_val:
                    try:
                        parsed = json.loads(raw_val)
                        # Filtramos filas completamente vacias para no guardar basura
                        cleaned_data[f_name] = [
                            row for row in parsed
                            if isinstance(row, dict) and any(v.strip() for v in row.values() if isinstance(v, str))
                        ]
                    except (json.JSONDecodeError, AttributeError):
                        cleaned_data[f_name] = []
                else:
                    cleaned_data[f_name] = []
                continue
                                                
        for f_name, f_config in schema_data.items():
            if f_name == "meta": continue
            
            if f_config.get("type") == "int":
                val = cleaned_data.get(f_name)
                if val is not None and not is_homebrew:
                    if "max_value" in f_config and val > f_config["max_value"]:
                        self.add_error(f_name, f"El valor no puede ser mayor a {f_config['max_value']}.")
                    if "min_value" in f_config and val < f_config["min_value"]:
                        self.add_error(f_name, f"El valor no puede ser menor a {f_config['min_value']}.")
                    if "max_field" in f_config:
                        max_ref_name = f_config["max_field"]
                        dyn_max = cleaned_data.get(max_ref_name)
                        if dyn_max is not None and val > dyn_max:
                            self.add_error(f_name, f"El valor no puede superar tu límite actual ({dyn_max}).")                            
                    if "min_field" in f_config:
                        min_ref_name = f_config["min_field"]
                        dyn_min = cleaned_data.get(min_ref_name)
                        if dyn_min is not None and val < dyn_min:
                            self.add_error(f_name, f"El valor no puede ser menor que tu límite actual ({dyn_min}).")

            if f_config.get("type") == "skill_list":
                raw_val = cleaned_data.get(f_name)
                parsed_data = {}
                if raw_val:
                    try:
                        parsed_data = json.loads(raw_val)
                    except json.JSONDecodeError:
                        pass
                                        
                is_manual = parsed_data.get("_meta", {}).get("manual_mode", False)
                formula_name = f_config.get("formula")
                catalog = f_config.get("catalog", [])                
                filter_by = f_config.get("filter_by")
                current_filter_val = cleaned_data.get(filter_by) if filter_by else None
                parsed_data, allowed_skill_ids = filter_skills(parsed_data, catalog, filter_by, current_filter_val)
                final_data = {"_meta": {"manual_mode": is_manual}}

                for skill in catalog:
                    skill_id = skill.get("id")
                    if skill_id not in allowed_skill_ids:
                        continue

                    skill_data = parsed_data.get(skill_id, {})
                    if not is_manual and formula_name and formula_name in BACKEND_FORMULAS:
                        prof_level = int(skill_data.get("prof", 0))
                        misc_val = int(skill_data.get("misc", 0)) if f_config.get(
                            "has_misc_bonus"
                        ) else 0
                        source_values = []
                        for src in skill.get("sources", []):
                            val = cleaned_data.get(src) or 0
                            try:
                                source_values.append(int(val))
                            except ValueError:
                                source_values.append(0)

                        formula_args = source_values + [
                            prof_level,
                            misc_val
                        ]

                        try:
                            try:
                                real_total = BACKEND_FORMULAS[
                                    formula_name
                                ](
                                    0,
                                    cleaned_data,
                                    None,
                                    formula_args
                                )
                            except TypeError:
                                real_total = BACKEND_FORMULAS[
                                    formula_name
                                ](
                                    0,
                                    cleaned_data,
                                    None
                                )
                        except Exception:
                            real_total = 0

                        final_data[skill_id] = {
                            "prof": prof_level,
                            "misc": misc_val,
                            "total": real_total
                        }
                    else:
                        if skill_id in parsed_data:
                            final_data[skill_id] = parsed_data[skill_id]

                cleaned_data[f_name] = final_data
                continue

            if "range_mapping" in f_config and "source_fields" in f_config and not is_homebrew:
                source_field = f_config["source_fields"][0]
                source_val = cleaned_data.get(source_field)
                
                if source_val in f_config["range_mapping"]:
                    limits = f_config["range_mapping"][source_val]
                    min_val = limits.get("min")
                    max_val = limits.get("max")
                    
                    target_val = cleaned_data.get(f_name)
                    if target_val is not None:
                        try:
                            target_val = int(target_val)
                            if min_val is not None and target_val < min_val:
                                self.add_error(f_name, f"El valor mínimo permitido es {min_val}.")
                            if max_val is not None and target_val > max_val:
                                self.add_error(f_name, f"El valor máximo permitido es {max_val}.")
                        except ValueError:
                            pass

        return cleaned_data    
    
    # Esta función inyecta la opción personalizada en el Select para que se vea correctamente al editar
    def custom_init(self, *args, **kwargs):
        forms.Form.__init__(self, *args, **kwargs)
        
        if 'custom_fields' in self.initial and isinstance(self.initial['custom_fields'], list):
            self.initial['custom_fields'] = json.dumps(self.initial['custom_fields'])
            
        for f_name, f_config in schema_data.items():
            if f_name == "meta": continue
            
            if f_config.get("type") in ["select", "choice"]:
                current_val = self.data.get(f_name) if self.is_bound else self.initial.get(f_name)
                field = self.fields.get(f_name)
                if current_val is not None and str(current_val).strip() != "" and field:
                    if str(current_val).strip() == "":
                        continue
                    existing_choices = [str(c[0]) for c in field.widget.choices]
                    if str(current_val) not in existing_choices:
                        field.widget.choices = list(field.widget.choices) + [(current_val, f"{current_val} (Homebrew)")]
                        
            if f_config.get("type") == "skill_list":
                current_val = self.initial.get(f_name)
                if isinstance(current_val, dict):
                    self.initial[f_name] = json.dumps(current_val)
            
            if f_config.get("type") == "str_list":
                current_val = self.initial.get(f_name)
                if isinstance(current_val, list):
                    self.initial[f_name] = json.dumps(current_val)

    form_fields['__init__'] = custom_init
    form_fields['clean'] = custom_clean
    DynamicCharacterForm = type('DynamicCharacterForm', (forms.Form,), form_fields)

    return DynamicCharacterForm

def filter_skills(parsed_data, catalog, filter_by, filter_val):
    #Elimina del JSON todas las skills que no esten permitidas segun el valor del campo filter_by.
    allowed_ids = set()
    for skill in catalog:
        allowed = skill.get("filter_values", [])
        if filter_by and filter_val:
            if allowed and filter_val not in allowed and "all" not in allowed:
                continue

        allowed_ids.add(skill["id"])

    # reconstruimos el JSON solo con las skills permitidas
    filtered = {"_meta": parsed_data.get("_meta", {})}
    for sid, sdata in parsed_data.items():
        if sid == "_meta":
            continue

        if sid in allowed_ids:
            filtered[sid] = sdata

    return filtered, allowed_ids

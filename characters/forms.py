from django import forms
import json
import math
from .models import Character

# Estas funciones son el espejo exacto del JS en create_character.html 
# Reciben: el valor original (val), todos los datos del formulario (data), y el mapa (mapping)
BACKEND_FORMULAS = {
    'map_value': lambda val, data, mapping: mapping.get(str(val), '') if mapping else '',
    'half_value': lambda val, data, mapping: math.floor(int(val or 0) / 2),
    'double_value': lambda val, data, mapping: math.floor(int(val or 0) * 2),
    'sum_values': lambda val, data, mapping: int(val or 0),
    'misc_only': lambda val, data, mapping, arr: arr[-1] if arr else 0,
    'dnd5e_2014_mod': lambda val, data, mapping: math.floor((int(val or 0) - 10) / 2),
    'dnd5e_2014_pb': lambda val, data, mapping: math.ceil((int(val or 0) / 4) + 1),
    'dnd5e_2014_skillcalc': lambda val, data, mapping, arr: (arr[0] if len(arr)>0 else 0) + ((arr[1] if len(arr)>1 else 0) * (arr[2] if len(arr)>2 else 0)),
    'pf1e_mod': lambda val, data, mapping: math.floor((int(val or 0) - 10) / 2),
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
}

class CharacterForm(forms.ModelForm):
    class Meta:
        model = Character
        fields = "__all__"

def create_character_form(schema_data):    
    form_fields = {}

    for field_name, field_config in schema_data.items():
        if field_name == "meta":
            continue

        widget_attrs = {}
        css_classes = "form-control"
        is_read_only = field_config.get("read_only", False)
        
        if is_read_only:
            widget_attrs['readonly'] = 'readonly'
            is_required = False 
            css_classes += " calculated-field"
            
            if "source_fields" in field_config:
                ids = [f"id_{sf}" for sf in field_config["source_fields"]]
                widget_attrs['data-source-ids'] = json.dumps(ids)
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
                int_kwargs['min_value'] = field_config["min_value"]
                widget_attrs['min'] = field_config["min_value"]
                
            if "max_value" in field_config and "range_mapping" not in field_config:
                int_kwargs['max_value'] = field_config["max_value"]
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

            form_fields[field_name] = forms.ChoiceField(
                label=label, choices=choices, required=is_required, 
                widget=forms.Select(attrs=widget_attrs), help_text=help_text,
                initial=default_value          
            )

        elif field_type == "skill_list":
            widget_attrs['data-is-skill-list'] = 'true'
            widget_attrs['data-catalog'] = json.dumps(field_config.get("catalog", []))
            widget_attrs['data-formula'] = field_config.get("formula", "")
            widget_attrs['data-allow-custom'] = str(field_config.get("allow_custom", False)).lower()
            widget_attrs['data-has-misc'] = "true" if field_config.get("has_misc_bonus") else "false"
            widget_attrs['data-filter-by'] = field_config.get("filter_by", "")
            
            form_fields[field_name] = forms.CharField(
                label=label,
                required=is_required,
                widget=forms.HiddenInput(attrs=widget_attrs),
                help_text=help_text,
                initial=default_value
            )

        else:
            form_fields[field_name] = forms.CharField(
                label=label, required=is_required, 
                widget=forms.TextInput(attrs=widget_attrs), help_text=help_text,
                initial=default_value
            )

    def custom_clean(self):
        cleaned_data = super(self.__class__, self).clean()
        
        for f_name, f_config in schema_data.items():
            if f_name == "meta": continue
            
            if f_config.get("read_only") and "formula" in f_config:
                formula_name = f_config["formula"]
                mapping = f_config.get("mapping", {})
                
                if formula_name in BACKEND_FORMULAS:
                    total_val = 0
                    source_values_arr = []
                    
                    if "source_fields" in f_config:
                        for sf in f_config["source_fields"]:
                            val = cleaned_data.get(sf) or 0
                            try:
                                val_int = int(val)
                                total_val += val_int
                                source_values_arr.append(val_int)
                            except ValueError:
                                source_values_arr.append(0)
                    elif "source_field" in f_config:
                        val = cleaned_data.get(f_config["source_field"]) or 0
                        try:
                            val_int = int(val)
                            total_val = val_int
                            source_values_arr.append(val_int)
                        except ValueError:
                            source_values_arr.append(0)
                        
                    try:
                        try:
                            real_value = BACKEND_FORMULAS[formula_name](total_val, cleaned_data, mapping, source_values_arr)
                        except TypeError:
                            real_value = BACKEND_FORMULAS[formula_name](total_val, cleaned_data, mapping)
                            
                        cleaned_data[f_name] = real_value
                    except Exception as e:
                        cleaned_data[f_name] = 0 if f_config.get("type") == "int" else ""
                                                
        for f_name, f_config in schema_data.items():
            if f_name == "meta": continue
            
            if f_config.get("type") == "int":
                val = cleaned_data.get(f_name)
                if val is not None:
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

            if "range_mapping" in f_config and "source_fields" in f_config:
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

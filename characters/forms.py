from django import forms
import json
import math
from .models import Character

# Estas funciones son el espejo exacto del JS en create_character.html 
# Reciben: el valor original (val), todos los datos del formulario (data), y el mapa (mapping)
BACKEND_FORMULAS = {
    'map_value': lambda val, data, mapping: mapping.get(str(val), '') if mapping else '',
    'half_value': lambda val, data, mapping: math.floor(int(val or 0) / 2),
    'sum_values': lambda val, data, mapping: int(val or 0),
    'dnd5e_2014_mod': lambda val, data, mapping: math.floor((int(val or 0) - 10) / 2),
    'pf1e_mod': lambda val, data, mapping: math.floor((int(val or 0) - 10) / 2),
    'coc7e_hp': lambda val, data, mapping: math.floor(BACKEND_FORMULAS['sum_values'](val, data, mapping) / 10),
    'coc7e_mp': lambda val, data, mapping: math.floor(int(val or 0) / 5),
    'vtm5e_healthmax': lambda val, data, mapping: math.floor(int(val or 0) + 3),        
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

        widget_attrs['class'] = css_classes        
        widget_attrs['placeholder'] = field_config.get("label", field_name.title())
        label = field_config.get("label", field_name.title())
        help_text = field_config.get("help_text", "")
        field_type = field_config.get("type", "string")

        if field_type == "int":
            int_kwargs = {
                'label': label,
                'required': is_required,
                'help_text': help_text,
            }
            
            if "min_value" in field_config:
                int_kwargs['min_value'] = field_config["min_value"]
                widget_attrs['min'] = field_config["min_value"]
                
            if "max_value" in field_config:
                int_kwargs['max_value'] = field_config["max_value"]
                widget_attrs['max'] = field_config["max_value"]

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
                widget=forms.Select(attrs=widget_attrs), help_text=help_text
            )
        else:
            form_fields[field_name] = forms.CharField(
                label=label, required=is_required, 
                widget=forms.TextInput(attrs=widget_attrs), help_text=help_text
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
                        
                        if "source_fields" in f_config:
                            for sf in f_config["source_fields"]:
                                val = cleaned_data.get(sf) or 0
                                try:
                                    total_val += int(val)
                                except ValueError:
                                    pass
                        elif "source_field" in f_config:
                            total_val = cleaned_data.get(f_config["source_field"])
                            
                        try:
                            real_value = BACKEND_FORMULAS[formula_name](total_val, cleaned_data, mapping)
                            cleaned_data[f_name] = real_value
                        except Exception as e:
                            cleaned_data[f_name] = 0 if f_config.get("type") == "int" else ""
                            
            return cleaned_data

    form_fields['clean'] = custom_clean
    DynamicCharacterForm = type('DynamicCharacterForm', (forms.Form,), form_fields)

    return DynamicCharacterForm

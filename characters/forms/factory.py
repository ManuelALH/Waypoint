from django import forms
import json

def create_character_form(schema_data):    
    # Este diccionario almacenará los campos (fields) que tendrá el formulario
    form_fields = {}

    for field_name, field_config in schema_data.items():
        if field_name == "meta":
            continue
        # ---------------------------------------------------------
        # 1. PREPARACIÓN DE ATRIBUTOS DEL WIDGET (HTML)
        # ---------------------------------------------------------
        widget_attrs = {}
        
        # A. Clase CSS base para que se vea bonito (Grid System)
        css_classes = "form-control"

        # B. Lógica para campos de Solo Lectura / Calculados
        is_read_only = field_config.get("read_only", False)
        
        if is_read_only:
            # Atributo HTML standard para no permitir escritura
            widget_attrs['readonly'] = 'readonly'
            # Clase CSS extra para pintarlo gris
            css_classes += " calculated-field"
            
            # C. Inyección de datos para el JavaScript (Motor de fórmulas)
            
            # Si depende de otro campo (ej: modifier depende de strength)
            if "source_field" in field_config:
                # Django genera IDs como 'id_nombrecampo', así que lo predecimos
                widget_attrs['data-source-id'] = f"id_{field_config['source_field']}"
            
            # Nombre de la fórmula a usar (ej: 'dnd5e_2014_mod')
            if "formula" in field_config:
                widget_attrs['data-formula'] = field_config['formula']
            
            # Si hay un mapa de valores (ej: para Hit Dice)
            if "mapping" in field_config:
                # Convertimos el dict de Python a string JSON para ponerlo en el HTML
                widget_attrs['data-mapping'] = json.dumps(field_config['mapping'])

        # Asignamos las clases finales al widget
        widget_attrs['class'] = css_classes
        
        # Opcional: Placeholder
        widget_attrs['placeholder'] = field_config.get("label", field_name.title())

        # ---------------------------------------------------------
        # 2. CREACIÓN DEL CAMPO DE DJANGO
        # ---------------------------------------------------------
        label = field_config.get("label", field_name.title())
        help_text = field_config.get("help_text", "")
        field_type = field_config.get("type", "string")
        
        # Los campos calculados no deben ser "required" para el usuario, 
        # ya que el JS los llena o el backend los ignora.
        is_required = not is_read_only

        if field_type == "int":
            form_fields[field_name] = forms.IntegerField(
                label=label,
                required=is_required,
                widget=forms.NumberInput(attrs=widget_attrs),
                help_text=help_text
            )

        elif field_type == "select" or field_type == "choice":
            # Manejo de opciones. El esquema puede traer una lista simple o pares clave-valor
            raw_choices = field_config.get("choices", [])
            choices = []
            
            if raw_choices:
                # Si es lista simple ['a', 'b'] -> convertimos a [('a','A'), ('b','B')]
                if not isinstance(raw_choices[0], (list, tuple)):
                    choices = [(c, c.title()) for c in raw_choices]
                else:
                    choices = raw_choices

            form_fields[field_name] = forms.ChoiceField(
                label=label,
                choices=choices,
                required=is_required,
                widget=forms.Select(attrs=widget_attrs),
                help_text=help_text
            )

        else: # Default a String / CharField
            form_fields[field_name] = forms.CharField(
                label=label,
                required=is_required,
                widget=forms.TextInput(attrs=widget_attrs),
                help_text=help_text
            )

    # ---------------------------------------------------------
    # 3. CONSTRUCCIÓN DE LA CLASE
    # ---------------------------------------------------------
    # Usamos type() para crear la clase al vuelo.
    # Nombre: DynamicCharacterForm
    # Hereda de: forms.Form
    # Atributos: form_fields
    DynamicCharacterForm = type('DynamicCharacterForm', (forms.Form,), form_fields)

    return DynamicCharacterForm
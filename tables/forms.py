from django import forms
from .models import Table
from gamesystems.models import GameSystem

class TableForm(forms.ModelForm):
    DAYS_OPTIONS = [
        ('Lunes', 'Lunes'),
        ('Martes', 'Martes'),
        ('Miércoles', 'Miércoles'),
        ('Jueves', 'Jueves'),
        ('Viernes', 'Viernes'),
        ('Sábado', 'Sábado'),
        ('Domingo', 'Domingo'),
    ]

    play_days = forms.MultipleChoiceField(
        choices=DAYS_OPTIONS,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'days-checkboxes'}),
        label="Días de Juego",
        required=False
    )

    class Meta:
        model = Table
        fields = [
            'name', 'system', 'description', 
            'modality', 'location', 'address', 
            'frequency', 'play_days', 
            'start_time', 'end_time',
            'experience_level', 'play_style', 'price_type', 
            'is_private'
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: La Maldición de Strahd'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe la trama, el tono de la partida y requisitos...'}),
            'location': forms.HiddenInput(),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Calle Falsa 123, Local 4 (Opcional)'}),
            'system': forms.Select(attrs={'class': 'form-select'}),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
            'modality': forms.Select(attrs={'class': 'form-select'}),
            'experience_level': forms.Select(attrs={'class': 'form-select'}),
            'play_style': forms.Select(attrs={'class': 'form-select'}),
            'price_type': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'is_private': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'privacyToggle'}),
        }

    def clean_play_days(self):
        days = self.cleaned_data.get('play_days')
        if not days:
            return ""
        return ", ".join(days)

    def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            # Verificamos si la instancia ya tiene una Primary Key (pk).
            # Si tiene PK, significa que la mesa ya existe en la BD (es una EDICIÓN).
            if self.instance and self.instance.pk:
                self.fields['system'].disabled = True            
                self.fields['system'].widget.attrs['style'] = 'background-color: #e9ecef; cursor: not-allowed;'
                
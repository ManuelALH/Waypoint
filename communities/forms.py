from django import forms
from .models import Community
from .models import Event

class CommunityForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = ['name', 'description', 'color', 'location', 'address']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej: La Hermandad de la Daga'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': '¿De qué trata esta comunidad? Normas, temática, etc.'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control form-control-color', 
                'type': 'color'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej: Av. Siempreviva 742, Local 5'
            }),
            'location': forms.HiddenInput(attrs={'id': 'id_location'}),
        }
        labels = {
            'name': 'Nombre de la Comunidad',
            'description': 'Descripción (Los primeros 32 carácteres se mostrarán en la lista de comunidades)',
            'color': 'Color Distintivo',
            'address': 'Sede / Dirección Física',
            'location': 'Ubicación Seleccionada',
        }
        help_texts = {
            'name': 'El nombre debe ser único y representativo de tu comunidad.',
            'description': 'Proporciona una descripción clara para atraer a los miembros adecuados.',
            'color': 'Elige un color que represente a tu comunidad en la plataforma.',
            'address': 'Si tu comunidad tiene una sede física, indícala aquí.',
            'location': 'Selecciona la ubicación en el mapa para mostrarla en tu comunidad.',
        }

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del gran encuentro'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '¿De qué trata el evento?'}),
            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
        labels = {
            'title': 'Título del Evento',
            'description': 'Descripción',
            'date': 'Fecha y Hora',
        }
        help_texts = {
            'title': 'El nombre del evento debe ser atractivo y descriptivo.',
            'description': 'Proporciona detalles sobre el evento para que los miembros sepan qué esperar.',
            'date': 'Selecciona la fecha y hora en la que se llevará a cabo el evento.',
        }
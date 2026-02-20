from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Correo Electrónico")

    class Meta:
        model = User
        fields = ("username", "email")

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está en uso. Por favor usa otro.")
        
        return email

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'avatar', 
            'bio',
            'email', 'is_email_public',
            'phone_number', 'is_phone_public',
            'location', 'is_location_public',
            'birth_date', 'is_birth_date_public',
            'gender', 'is_gender_public',
            'experience_level', 
            'play_style', 
            'favorite_system',
            'is_last_login_public',
        ]
        
        widgets = {
            'avatar': forms.RadioSelect(),
            'bio': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Cuéntanos algo sobre ti...'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ejemplo@correo.com'}),
            'is_email_public': forms.CheckboxInput(attrs={'class': 'hidden-checkbox'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+52...'}),
            'is_phone_public': forms.CheckboxInput(attrs={'class': 'hidden-checkbox'}),
            'is_location_public': forms.CheckboxInput(attrs={'class': 'hidden-checkbox'}),
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'is_birth_date_public': forms.CheckboxInput(attrs={'class': 'hidden-checkbox'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'is_gender_public': forms.CheckboxInput(attrs={'class': 'hidden-checkbox'}),
            'experience_level': forms.Select(attrs={'class': 'form-control'}),
            'play_style': forms.Select(attrs={'class': 'form-control'}),
            'favorite_system': forms.Select(attrs={'class': 'form-control'}),
            'is_last_login_public': forms.CheckboxInput(attrs={'class': 'hidden-checkbox'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['avatar'].widget = forms.RadioSelect(choices=self._meta.model.Avatar.choices)

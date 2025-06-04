# main/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    telephone = forms.CharField(max_length=15, required=False)
    adresse = forms.CharField(widget=forms.Textarea, required=False)
    
    ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('docteur', 'Docteur'),
        ('infirmier', 'Infirmier'),
        ('secretaire', 'Secrétaire'),
    ]
    
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2', 'role', 'telephone', 'adresse')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = self.cleaned_data['role']
        user.telephone = self.cleaned_data['telephone']
        user.adresse = self.cleaned_data['adresse']
        
        if commit:
            user.save()
        return user
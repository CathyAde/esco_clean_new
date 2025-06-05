from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, RendezVous, Patient, Medecin, Infirmier, Secretaire

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")
    first_name = forms.CharField(max_length=30, required=True, label="Prénom")
    last_name = forms.CharField(max_length=30, required=True, label="Nom")
    telephone = forms.CharField(max_length=15, required=False, label="Téléphone")
    role = forms.ChoiceField(choices=CustomUser.ROLES, required=True, label="Rôle")
    
    # Champs conditionnels selon le rôle
    specialite = forms.CharField(max_length=100, required=False, label="Spécialité")
    service = forms.CharField(max_length=100, required=False, label="Service")
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'telephone', 'role', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Supprimer les textes d'aide par défaut
        self.fields['username'].help_text = None
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None
        
        # Personnaliser les messages d'erreur
        self.fields['username'].error_messages = {
            'required': 'Le nom d\'utilisateur est obligatoire.',
            'unique': 'Ce nom d\'utilisateur existe déjà.'
        }
        self.fields['email'].error_messages = {
            'required': 'L\'email est obligatoire.',
            'invalid': 'Veuillez entrer une adresse email valide.'
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Cette adresse email est déjà utilisée.")
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        
        # Validation selon le rôle
        if role == 'docteur' and not cleaned_data.get('specialite'):
            self.add_error('specialite', 'La spécialité est requise pour les médecins.')
        
        if role in ['infirmier', 'secretaire'] and not cleaned_data.get('service'):
            self.add_error('service', 'Le service est requis pour ce rôle.')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.telephone = self.cleaned_data.get('telephone', '')
        user.role = self.cleaned_data['role']
        user.specialite = self.cleaned_data.get('specialite', '')
        
        if commit:
            user.save()
            # Créer le profil spécialisé selon le rôle
            self._create_specialized_profile(user)
        
        return user
    
    def _create_specialized_profile(self, user):
        """Crée le profil spécialisé selon le rôle de l'utilisateur"""
        try:
            if user.role == 'patient':
                Patient.objects.create(user=user)
            elif user.role == 'docteur':
                Medecin.objects.create(
                    user=user,
                    specialite=self.cleaned_data.get('specialite', '')
                )
            elif user.role == 'infirmier':
                Infirmier.objects.create(
                    user=user,
                    service=self.cleaned_data.get('service', '')
                )
            elif user.role == 'secretaire':
                Secretaire.objects.create(
                    user=user,
                    service=self.cleaned_data.get('service', '')
                )
        except Exception as e:
            print(f"Erreur lors de la création du profil spécialisé: {e}")

class RendezVousForm(forms.ModelForm):
    date_rdv = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Date du rendez-vous"
    )
    heure_rdv = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        label="Heure du rendez-vous"
    )
    
    class Meta:
        model = RendezVous
        fields = ['medecin', 'date_rdv', 'heure_rdv', 'motif']
        widgets = {
            'motif': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'medecin': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'medecin': 'Médecin',
            'motif': 'Motif de consultation'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer pour ne montrer que les médecins
        self.fields['medecin'].queryset = CustomUser.objects.filter(role='docteur', is_active=True)
        self.fields['medecin'].empty_label = "Choisir un médecin..."

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'telephone', 'adresse']
        widgets = {
            'adresse': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'first_name': 'Prénom',
            'last_name': 'Nom',
            'email': 'Email',
            'telephone': 'Téléphone',
            'adresse': 'Adresse',
        }
        # from django import forms
# from django.contrib.auth.forms import UserCreationForm
# from .models import CustomUser, RendezVous, Patient, Medecin, Infirmier, Secretaire

# class CustomUserCreationForm(UserCreationForm):
#     email = forms.EmailField(required=True)
#     first_name = forms.CharField(max_length=30, required=True, label="Prénom")
#     last_name = forms.CharField(max_length=30, required=True, label="Nom")
#     telephone = forms.CharField(max_length=15, required=False)
#     role = forms.ChoiceField(choices=CustomUser.ROLES, required=True, label="Rôle")
    
#     # Champs conditionnels selon le rôle
#     specialite = forms.CharField(max_length=100, required=False, label="Spécialité")
#     numero_licence = forms.CharField(max_length=50, required=False, label="Numéro de licence")
#     service = forms.CharField(max_length=100, required=False, label="Service")
    
#     class Meta:
#         model = CustomUser
#         fields = ('username', 'email', 'first_name', 'last_name', 'telephone', 'role', 'password1', 'password2')
    
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['username'].help_text = None
#         self.fields['password1'].help_text = None
#         self.fields['password2'].help_text = None
    
#     def clean(self):
#         cleaned_data = super().clean()
#         role = cleaned_data.get('role')
        
#         # Validation selon le rôle
#         if role in ['docteur', 'infirmier'] and not cleaned_data.get('specialite'):
#             if role == 'docteur':
#                 self.add_error('specialite', 'La spécialité est requise pour les médecins.')
#             elif role == 'infirmier':
#                 self.add_error('service', 'Le service est requis pour les infirmiers.')
        
#         return cleaned_data
    
#     def save(self, commit=True):
#         user = super().save(commit=False)
#         user.email = self.cleaned_data['email']
#         user.first_name = self.cleaned_data['first_name']
#         user.last_name = self.cleaned_data['last_name']
#         user.telephone = self.cleaned_data['telephone']
#         user.role = self.cleaned_data['role']
#         user.specialite = self.cleaned_data.get('specialite', '')
#         user.numero_licence = self.cleaned_data.get('numero_licence', '')
        
#         if commit:
#             user.save()
#             # Créer le profil spécialisé selon le rôle
#             self._create_specialized_profile(user)
        
#         return user
    
#     def _create_specialized_profile(self, user):
#         """Crée le profil spécialisé selon le rôle de l'utilisateur"""
#         if user.role == 'patient':
#             Patient.objects.create(user=user)
#         elif user.role == 'docteur':
#             Medecin.objects.create(
#                 user=user,
#                 specialite=self.cleaned_data.get('specialite', '')
#             )
#         elif user.role == 'infirmier':
#             Infirmier.objects.create(
#                 user=user,
#                 service=self.cleaned_data.get('service', '')
#             )
#         elif user.role == 'secretaire':
#             Secretaire.objects.create(
#                 user=user,
#                 service=self.cleaned_data.get('service', '')
#             )

# class RendezVousForm(forms.ModelForm):
#     date_rdv = forms.DateField(
#         widget=forms.DateInput(attrs={'type': 'date'}),
#         label="Date"
#     )
#     heure_rdv = forms.TimeField(
#         widget=forms.TimeInput(attrs={'type': 'time'}),
#         label="Heure"
#     )
    
#     class Meta:
#         model = RendezVous
#         fields = ['medecin', 'motif']
#         widgets = {
#             'motif': forms.Textarea(attrs={'rows': 3}),
#         }
    
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # Filtrer pour ne montrer que les médecins actifs
#         self.fields['medecin'].queryset = CustomUser.objects.filter(role='docteur', is_active=True)
#         self.fields['medecin'].empty_label = "Choisir un médecin..."

# class ProfileUpdateForm(forms.ModelForm):
#     class Meta:
#         model = CustomUser
#         fields = ['first_name', 'last_name', 'email', 'telephone', 'adresse']
#         widgets = {
#             'adresse': forms.Textarea(attrs={'rows': 3}),
#         }
#         labels = {
#             'first_name': 'Prénom',
#             'last_name': 'Nom',
#             'email': 'Email',
#             'telephone': 'Téléphone',
#             'adresse': 'Adresse',
#         }# # main/forms.py
# # from django import forms
# # from django.contrib.auth.forms import UserCreationForm
# # from .models import CustomUser

# # class CustomUserCreationForm(UserCreationForm):
# #     email = forms.EmailField(required=True)
# #     telephone = forms.CharField(max_length=15, required=False)
# #     adresse = forms.CharField(widget=forms.Textarea, required=False)
    
# #     ROLE_CHOICES = [
# #         ('patient', 'Patient'),
# #         ('docteur', 'Docteur'),
# #         ('infirmier', 'Infirmier'),
# #         ('secretaire', 'Secrétaire'),
# #     ]
    
# #     role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)

# #     class Meta:
# #         model = CustomUser
# #         fields = ('username', 'email', 'password1', 'password2', 'role', 'telephone', 'adresse')

# #     def save(self, commit=True):
# #         user = super().save(commit=False)
# #         user.email = self.cleaned_data['email']
# #         user.role = self.cleaned_data['role']
# #         user.telephone = self.cleaned_data['telephone']
# #         user.adresse = self.cleaned_data['adresse']
        
# #         if commit:
# #             user.save()
# #         return user
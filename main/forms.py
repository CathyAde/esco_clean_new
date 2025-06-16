
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, RendezVous, Patient, Medecin, Infirmier, Secretaire
# Dans forms.py - CORRECT ✅
from .models import Consultation


# class CustomUserCreationForm(UserCreationForm):
#     email = forms.EmailField(required=True, label="Email")
#     first_name = forms.CharField(max_length=30, required=True, label="Prénom")
#     last_name = forms.CharField(max_length=30, required=True, label="Nom")
#     telephone = forms.CharField(max_length=15, required=False, label="Téléphone")
#     role = forms.ChoiceField(choices=CustomUser.ROLES, required=True, label="Rôle")
    
#     # Champs conditionnels selon le rôle
#     specialite = forms.CharField(max_length=100, required=False, label="Spécialité")
#     service = forms.CharField(max_length=100, required=False, label="Service")
    
#     class Meta:
#         model = CustomUser
#         fields = ('username', 'email', 'first_name', 'last_name', 'telephone', 'role', 'password1', 'password2')
# Dans forms.py, trouve la ligne avec l'erreur et corrige :

class CustomUserCreationForm(UserCreationForm):
    # 🔧 CORRECTION : utilise ROLE_CHOICES au lieu de ROLES
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, required=True, label="Rôle")
    #                               ^^^^^^^^^^^^^^^^^^^
    
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('email', 'first_name', 'last_name', 'role')
            
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


# Dans main/forms.py - REMPLACEZ complètement la classe RendezVousForm
class RendezVousForm(forms.ModelForm):
    
    heure_rdv = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        required=True
    )
     
    class Meta:
        model = RendezVous
        fields = ['patient', 'medecin', 'date_rdv', 'heure_rdv', 'motif']  # ⭐ Ajouter 'patient'
        widgets = {
            'date_rdv': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'heure_rdv': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'motif': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'patient': forms.Select(attrs={'class': 'form-select'}),  # ⭐ Ajouter le widget patient
            'medecin': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        medecins = kwargs.pop('medecins', None)
        super().__init__(*args, **kwargs)

        # Queryset pour les médecins
        if medecins is not None:
            self.fields['medecin'].queryset = medecins
        else:
            self.fields['medecin'].queryset = CustomUser.objects.filter(role='docteur', is_active=True)

        # Queryset pour les patients ⭐ AJOUTER CETTE LIGNE
        self.fields['patient'].queryset = CustomUser.objects.filter(role='patient', is_active=True)

        # Labels
        self.fields['medecin'].label = "Choisir un médecin"
        self.fields['patient'].label = "Choisir un patient"  # ⭐ AJOUTER ce label
        self.fields['medecin'].empty_label = "-- Sélectionner un médecin --"
        self.fields['patient'].empty_label = "-- Sélectionner un patient --"  # ⭐ AJOUTER ceci
        
        self.fields['medecin'].widget.attrs.update({
            'class': 'form-select',
            'required': 'required'
        })
        self.fields['patient'].widget.attrs.update({  # ⭐ AJOUTER ceci
            'class': 'form-select',
            'required': 'required'
        })
        
        # Fonction pour afficher les noms des médecins
        self.fields['medecin'].label_from_instance = lambda obj: f"Dr. {obj.get_full_name()} - {obj.specialite or 'Généraliste'}"
        # Fonction pour afficher les noms des patients ⭐ AJOUTER ceci
        self.fields['patient'].label_from_instance = lambda obj: f"{obj.get_full_name() or obj.username}"
    
    

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'telephone', 'adresse']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
        labels = {
            'first_name': 'Prénom',
            'last_name': 'Nom',
            'email': 'Email',
            'telephone': 'Téléphone',
            'adresse': 'Adresse',
        }

# Ajoute ça à la fin de ton fichier forms.py
class ConsultationForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ['symptomes', 'diagnostic', 'traitement', 'observations']
        widgets = {
            'symptomes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Décrivez les symptômes du patient...'}),
            'diagnostic': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Diagnostic médical...'}),
            'traitement': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Traitement prescrit...'}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observations complémentaires...'}),
        }
        labels = {
            'symptomes': 'Symptômes',
            'diagnostic': 'Diagnostic',
            'traitement': 'Traitement',
            'observations': 'Observations',
        }   
            
# Dans forms.py, ajoute :

class ProfilMedicalForm(forms.ModelForm):
    """Formulaire pour le profil médical du patient"""
    
    class Meta:
        model = CustomUser
        fields = [
            'date_naissance', 'poids', 'taille', 'tension_systolique', 'tension_diastolique',
            'groupe_sanguin', 'allergies', 'antecedents_medicaux', 'medicaments_actuels',
            'personne_urgence_nom', 'personne_urgence_tel'
        ]
        widgets = {
            'date_naissance': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'poids': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'placeholder': 'kg'}),
            'taille': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'placeholder': 'cm'}),
            'tension_systolique': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': 'Ex: 120'}),
            'tension_diastolique': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': 'Ex: 80'}),
            'groupe_sanguin': forms.Select(attrs={'class': 'form-select'}),
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Indiquez vos allergies connues...'}),
            'antecedents_medicaux': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Maladies antérieures, opérations...'}),
            'medicaments_actuels': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Médicaments que vous prenez actuellement...'}),
            'personne_urgence_nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de la personne à contacter'}),
            'personne_urgence_tel': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numéro de téléphone'}),
        }
        
    def clean_poids(self):
        poids = self.cleaned_data.get('poids')
        if poids and (poids <= 0 or poids > 300):
            raise forms.ValidationError("Le poids doit être entre 1 et 300 kg.")
        return poids
    
    def clean_taille(self):
        taille = self.cleaned_data.get('taille')
        if taille and (taille <= 0 or taille > 250):
            raise forms.ValidationError("La taille doit être entre 1 et 250 cm.")
        return taille
    
    def clean_tension_systolique(self):
        tension = self.cleaned_data.get('tension_systolique')
        if tension and (tension <= 0 or tension > 300):
            raise forms.ValidationError("La tension systolique doit être entre 1 et 300.")
        return tension
    
    def clean_tension_diastolique(self):
        tension = self.cleaned_data.get('tension_diastolique')
        if tension and (tension <= 0 or tension > 200):
            raise forms.ValidationError("La tension diastolique doit être entre 1 et 200.")
        return tension     
     

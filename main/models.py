from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('docteur', 'Docteur'),
        ('infirmier', 'Infirmier'),
        ('secretaire', 'Secrétaire'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')
    telephone = models.CharField(max_length=15, blank=True, default='')
    adresse = models.TextField(blank=True, default='')
    date_naissance = models.DateField(null=True, blank=True)
    specialite = models.CharField(max_length=100, blank=True, default='')  # Pour médecins
    numero_licence = models.CharField(max_length=50, blank=True, default='')  # Pour médecins/infirmiers

    def __str__(self):
        return f"{self.username} ({self.role})"

class Patient(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    numero_patient = models.CharField(max_length=20, unique=True)
    groupe_sanguin = models.CharField(max_length=5, blank=True)
    allergies = models.TextField(blank=True)
    antecedents = models.TextField(blank=True)
    
    def __str__(self):
        return f"Patient {self.user.username}"

class RendezVous(models.Model):
    STATUS_CHOICES = [
        ('programme', 'Programmé'),
        ('confirme', 'Confirmé'),
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('annule', 'Annulé'),
    ]
    
    patient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='rdv_patient')
    medecin = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='rdv_medecin')
    date_rdv = models.DateTimeField()
    motif = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='programme')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"RDV {self.patient.username} - {self.medecin.username} ({self.date_rdv})"

class Consultation(models.Model):
    rdv = models.OneToOneField(RendezVous, on_delete=models.CASCADE)
    symptomes = models.TextField()
    diagnostic = models.TextField()
    traitement = models.TextField()
    observations = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Consultation {self.rdv.patient.username}"

class SoinsInfirmier(models.Model):
    TYPE_CHOICES = [
        ('pansement', 'Pansement'),
        ('injection', 'Injection'),
        ('perfusion', 'Perfusion'),
        ('prise_constantes', 'Prise des constantes'),
        ('medicaments', 'Administration médicaments'),
        ('autre', 'Autre'),
    ]
    
    patient = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    infirmier = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='soins_infirmier')
    type_soin = models.CharField(max_length=50, choices=TYPE_CHOICES)
    description = models.TextField()
    date_soin = models.DateTimeField()
    observations = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Soin {self.type_soin} - {self.patient.username}"

class Planning(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    disponible = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Planning {self.user.username} - {self.date}"

# from django.contrib.auth.models import AbstractUser
# from django.db import models

# class CustomUser(AbstractUser):
#     ROLE_CHOICES = [
#         ('patient', 'Patient'),
#         ('docteur', 'Docteur'),
#         ('infirmier', 'Infirmier'),
#         ('secretaire', 'Secrétaire'),
#     ]
    
#     role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')
#     telephone = models.CharField(max_length=15, blank=True, default='')
#     adresse = models.TextField(blank=True, default='')

#     def __str__(self):
#         return f"{self.username} ({self.role})"
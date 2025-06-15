from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid
from datetime import time

class CustomUser(AbstractUser):
    ROLES = [
        ('patient', 'Patient'),
        ('docteur', 'Médecin'),
        ('infirmier', 'Infirmier'),
        ('secretaire', 'Secrétaire'),
        ('administrateur', 'Administrateur'),
    ]
    
    # ID unique pour chaque utilisateur
    user_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLES, default='patient')
    telephone = models.CharField(max_length=15, blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    date_naissance = models.DateField(blank=True, null=True)
    specialite = models.CharField(max_length=100, blank=True, null=True)
    numero_licence = models.CharField(max_length=50, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.user_id:
            # Générer un ID unique basé sur le rôle
            if self.role == 'patient':
                self.user_id = f"PAT{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4().hex[:6]).upper()}"
            elif self.role == 'docteur':
                self.user_id = f"DOC{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4().hex[:6]).upper()}"
            elif self.role == 'infirmier':
                self.user_id = f"INF{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4().hex[:6]).upper()}"
            elif self.role == 'secretaire':
                self.user_id = f"SEC{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4().hex[:6]).upper()}"
            else:
                self.user_id = f"ADM{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4().hex[:6]).upper()}"
        super().save(*args, **kwargs)
    
    
    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.username
class Patient(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    numero_patient = models.CharField(max_length=20, unique=True, blank=True, null=True)
    groupe_sanguin = models.CharField(max_length=5, blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    antecedents = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Champs médicaux enrichis
    poids = models.FloatField(blank=True, null=True, help_text="Poids en kg")
    taille = models.FloatField(blank=True, null=True, help_text="Taille en cm")
    profession = models.CharField(max_length=100, blank=True, null=True)
    situation_familiale = models.CharField(max_length=50, blank=True, null=True)
    personne_contact = models.CharField(max_length=100, blank=True, null=True)
    tel_contact = models.CharField(max_length=15, blank=True, null=True)
    medecin_traitant = models.CharField(max_length=100, blank=True, null=True)
    assurance = models.CharField(max_length=100, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.numero_patient:
            self.numero_patient = self.user.user_id
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Patient {self.numero_patient} - {self.user.username}"
    
    def get_nom_complet(self):
        if self.user.first_name or self.user.last_name:
            return f"{self.user.first_name} {self.user.last_name}".strip()
        return self.user.username

class Medecin(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    numero_ordre = models.CharField(max_length=50, unique=True, blank=True, null=True)
    specialite = models.CharField(max_length=100, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.numero_ordre:
            self.numero_ordre = self.user.user_id
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Dr. {self.user.get_full_name() or self.user.username}"

class Infirmier(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    numero_ordre = models.CharField(max_length=50, unique=True, blank=True, null=True)
    service = models.CharField(max_length=100, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.numero_ordre:
            self.numero_ordre = self.user.user_id
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Inf. {self.user.get_full_name() or self.user.username}"

class Secretaire(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    service = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"Sec. {self.user.get_full_name() or self.user.username}"

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
    date_rdv = models.DateField()
    heure_rdv = models.TimeField(default=time(9, 0))  # ← UNE SEULE définition avec valeur par défaut
    motif = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='programme')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Rendez-vous"
        verbose_name_plural = "Rendez-vous"
        ordering = ['-date_rdv', '-heure_rdv']
    
    def __str__(self):
        return f"RDV {self.patient.username} - Dr. {self.medecin.username} - {self.date_rdv} {self.heure_rdv}"
    
    def clean(self):
        """Validation personnalisée"""
        from django.core.exceptions import ValidationError
        from django.utils import timezone
        import datetime
        
        # Vérifier que la date n'est pas dans le passé
        if self.date_rdv and self.date_rdv < timezone.now().date():
            raise ValidationError("La date du rendez-vous ne peut pas être dans le passé.")
        
        # Vérifier que l'heure n'est pas dans le passé pour aujourd'hui
        if (self.date_rdv == timezone.now().date() and 
            self.heure_rdv and 
            self.heure_rdv < timezone.now().time()):
            raise ValidationError("L'heure du rendez-vous ne peut pas être dans le passé.")
    
    @property
    def date_heure_complete(self):
        """Combine la date et l'heure pour l'affichage"""
        from datetime import datetime, time
        return datetime.combine(self.date_rdv, self.heure_rdv or time(9, 0))

class Consultation(models.Model):
    rdv = models.OneToOneField(RendezVous, on_delete=models.CASCADE, related_name='consultation')
    rdv = models.OneToOneField(RendezVous, on_delete=models.CASCADE)
    symptomes = models.TextField(blank=True, null=True)
    diagnostic = models.TextField(blank=True, null=True)
    traitement = models.TextField(blank=True, null=True)
    observations = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Consultation {self.rdv.patient.username} - {self.rdv.date_rdv.strftime('%d/%m/%Y')}"

class SoinsInfirmier(models.Model):
    TYPE_SOIN_CHOICES = [
        ('pansement', 'Pansement'),
        ('injection', 'Injection'),
        ('perfusion', 'Perfusion'),
        ('prise_constantes', 'Prise de constantes'),
        ('medicament', 'Administration médicament'),
        ('autre', 'Autre'),
    ]
    
    patient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='soins_patient')
    infirmier = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='soins_infirmier')
    type_soin = models.CharField(max_length=30, choices=TYPE_SOIN_CHOICES)
    description = models.TextField()
    date_soin = models.DateTimeField()
    observations = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Soin infirmier"
        verbose_name_plural = "Soins infirmiers"
        ordering = ['-date_soin']
    
    def __str__(self):
        return f"Soin {self.get_type_soin_display()} - {self.patient.username} - {self.date_soin.strftime('%d/%m/%Y')}"

class Planning(models.Model):
    JOURS_SEMAINE = [
        ('lundi', 'Lundi'),
        ('mardi', 'Mardi'),
        ('mercredi', 'Mercredi'),
        ('jeudi', 'Jeudi'),
        ('vendredi', 'Vendredi'),
        ('samedi', 'Samedi'),
        ('dimanche', 'Dimanche'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    jour = models.CharField(max_length=10, choices=JOURS_SEMAINE, default='lundi')
    heure_debut = models.TimeField(default='09:00')
    heure_fin = models.TimeField(default='17:00')
    disponible = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'jour', 'heure_debut']
        ordering = ['jour', 'heure_debut']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_jour_display()} {self.heure_debut}-{self.heure_fin}"# from django.contrib.auth.models import AbstractUser
class Prescription(models.Model):
    medecin = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='prescriptions_medecin')
    patient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='prescriptions_patient')
    contenu = models.TextField()
    date_prescription = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_prescription']
    
    def __str__(self):
        return f"Prescription {self.patient.get_full_name()} - {self.date_prescription.strftime('%d/%m/%Y')}"
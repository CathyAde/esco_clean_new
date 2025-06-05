#!/usr/bin/env python
import os
import sys
import django
from django.utils import timezone
from datetime import datetime, timedelta

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esco_clean.settings')
django.setup()

from main.models import CustomUser, Patient, Medecin, Infirmier, Secretaire, RendezVous, Consultation

def populate_database():
    print("🏥 Création des données de test pour ESCO...")
    
    # 1. Créer des médecins
    print("👨‍⚕️ Création des médecins...")
    medecin1 = CustomUser.objects.create_user(
        username='dr_martin',
        email='dr.martin@esco.com',
        password='password123',
        first_name='Jean',
        last_name='Martin',
        role='docteur',
        specialite='Cardiologie',
        telephone='0123456789'
    )
    Medecin.objects.create(user=medecin1, specialite='Cardiologie')
    
    medecin2 = CustomUser.objects.create_user(
        username='dr_dubois',
        email='dr.dubois@esco.com',
        password='password123',
        first_name='Marie',
        last_name='Dubois',
        role='docteur',
        specialite='Pédiatrie',
        telephone='0123456790'
    )
    Medecin.objects.create(user=medecin2, specialite='Pédiatrie')
    
    # 2. Créer des infirmiers
    print("👩‍⚕️ Création des infirmiers...")
    infirmier1 = CustomUser.objects.create_user(
        username='inf_claire',
        email='claire@esco.com',
        password='password123',
        first_name='Claire',
        last_name='Bernard',
        role='infirmier',
        telephone='0123456791'
    )
    Infirmier.objects.create(user=infirmier1, service='Cardiologie')
    
    # 3. Créer des secrétaires
    print("👔 Création des secrétaires...")
    secretaire1 = CustomUser.objects.create_user(
        username='sec_sophie',
        email='sophie@esco.com',
        password='password123',
        first_name='Sophie',
        last_name='Moreau',
        role='secretaire',
        telephone='0123456792'
    )
    Secretaire.objects.create(user=secretaire1, service='Accueil')
    
    # 4. Créer des patients
    print("🤕 Création des patients...")
    patient1 = CustomUser.objects.create_user(
        username='patient_paul',
        email='paul@email.com',
        password='password123',
        first_name='Paul',
        last_name='Durand',
        role='patient',
        telephone='0123456793'
    )
    Patient.objects.create(
        user=patient1,
        groupe_sanguin='A+',
        allergies='Pénicilline',
        antecedents='Hypertension'
    )
    
    patient2 = CustomUser.objects.create_user(
        username='patient_alice',
        email='alice@email.com',
        password='password123',
        first_name='Alice',
        last_name='Roux',
        role='patient',
        telephone='0123456794'
    )
    Patient.objects.create(
        user=patient2,
        groupe_sanguin='O-',
        allergies='Aucune',
        antecedents='Diabète type 2'
    )
    
    # 5. Créer des rendez-vous
    print("📅 Création des rendez-vous...")
    rdv1 = RendezVous.objects.create(
        patient=patient1,
        medecin=medecin1,
        date_rdv=timezone.now() + timedelta(days=1),
        motif='Contrôle cardiaque',
        status='confirme'
    )
    
    rdv2 = RendezVous.objects.create(
        patient=patient2,
        medecin=medecin2,
        date_rdv=timezone.now() + timedelta(days=2),
        motif='Consultation pédiatrique',
        status='programme'
    )
    
    # 6. Créer une consultation
    print("🩺 Création des consultations...")
    Consultation.objects.create(
        rdv=rdv1,
        symptomes='Douleurs thoraciques',
        diagnostic='Angine de poitrine',
        traitement='Repos, médicaments prescrits',
        observations='Patient à surveiller'
    )
    
    print("✅ Base de données peuplée avec succès!")
    print(f"👥 Utilisateurs créés : {CustomUser.objects.count()}")
    print(f"🤕 Patients : {Patient.objects.count()}")
    print(f"👨‍⚕️ Médecins : {Medecin.objects.count()}")
    print(f"📅 Rendez-vous : {RendezVous.objects.count()}")

if __name__ == '__main__':
    populate_database()
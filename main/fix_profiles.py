# fix_profiles.py - À exécuter une fois
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'votre_projet.settings')
django.setup()

from main.models import CustomUser, Patient, Medecin, Infirmier, Secretaire

def fix_existing_profiles():
    """Créer les profils manquants pour les utilisateurs existants"""
    users = CustomUser.objects.all()
    
    for user in users:
        print(f"🔍 Traitement de {user.username} (rôle: {user.role})")
        
        if user.role == 'patient':
            patient, created = Patient.objects.get_or_create(user=user)
            if created:
                print(f"✅ Profil Patient créé pour {user.username}")
            else:
                print(f"ℹ️  Profil Patient existant pour {user.username}")
                
        elif user.role == 'docteur':
            medecin, created = Medecin.objects.get_or_create(
                user=user,
                defaults={'specialite': user.specialite or 'Généraliste'}
            )
            if created:
                print(f"✅ Profil Médecin créé pour {user.username}")
            else:
                print(f"ℹ️  Profil Médecin existant pour {user.username}")
                
        elif user.role == 'infirmier':
            infirmier, created = Infirmier.objects.get_or_create(user=user)
            if created:
                print(f"✅ Profil Infirmier créé pour {user.username}")
                
        elif user.role == 'secretaire':
            secretaire, created = Secretaire.objects.get_or_create(user=user)
            if created:
                print(f"✅ Profil Secrétaire créé pour {user.username}")

if __name__ == '__main__':
    fix_existing_profiles()
    print("🎉 Réparation terminée !")
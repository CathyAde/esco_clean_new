import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'votre_projet.settings')
django.setup()

from main.models import CustomUser, Medecin

def create_doctor():
    # Créer l'utilisateur
    user = CustomUser.objects.create_user(
        username='dr_martin',
        email='dr.martin@esco.com',
        first_name='Pierre',
        last_name='Martin',
        role='docteur',
        specialite='Cardiologie',
        password='motdepasse123'
    )
    
    # Le signal devrait créer automatiquement le profil Medecin
    print(f"✅ Médecin créé: {user.username}")
    
    # Vérifier si le profil existe
    try:
        medecin = Medecin.objects.get(user=user)
        print(f"✅ Profil médecin trouvé: {medecin}")
    except Medecin.DoesNotExist:
        # Créer manuellement si le signal a échoué
        medecin = Medecin.objects.create(user=user, specialite='Cardiologie')
        print(f"✅ Profil médecin créé manuellement: {medecin}")

if __name__ == '__main__':
    create_doctor()
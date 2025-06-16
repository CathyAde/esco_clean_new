from django.urls import path
from . import views

urlpatterns = [
    # Page d'accueil
    path('', views.home, name='home'),
    
    # Authentification
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('inscription/', views.inscription, name='inscription'),
    
    # Dashboards
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/patient/', views.dashboard_patient, name='dashboard_patient'),
    path('dashboard/medecin/', views.dashboard_medecin, name='dashboard_medecin'),
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    path('dashboard/infirmier/', views.dashboard_infirmier, name='dashboard_infirmier'),
    path('dashboard/secretaire/', views.dashboard_secretaire, name='dashboard_secretaire'),
    
    # Rendez-vous
    path('nouveau-rdv/', views.nouveau_rdv, name='nouveau_rdv'),
    path('mes-rdv/', views.mes_rdv, name='mes_rdv'),
    
    # URLs Patients
    path('consultations/', views.consultations, name='consultations'),
    path('mon-dossier-medical/', views.mon_dossier_medical, name='mon_dossier_medical'),
    path('download-dossier-pdf/', views.download_my_dossier_pdf, name='download_my_dossier_pdf'),
    
    # URLs Médecin
    path('nouvelle-consultation/', views.nouvelle_consultation, name='nouvelle_consultation'),
    path('consultations-medecin/', views.consultations_medecin, name='consultations_medecin'),
    path('liste-patients/', views.liste_patients, name='liste_patients'),
    # Vérifie que cette ligne existe dans urls.py
    path('rdv-medecin/', views.rdv_medecin, name='rdv_medecin'),
    path('planning-medecin/', views.planning_medecin, name='planning_medecin'),
    # Dans urls.py, ajoute cette ligne dans urlpatterns
    path('nouvelle-prescription/', views.nouvelle_prescription, name='nouvelle_prescription'),
    # Profil
    path('profile/', views.profile, name='profile'),
    # Dans urls.py, ajoute ces lignes :
    path('mes-prescriptions/', views.mes_prescriptions, name='mes_prescriptions'),
    path('dossier-patient/<int:patient_id>/', views.dossier_patient, name='dossier_patient'),
    # Dans urls.py, ajoute :
    path('profil-medical/', views.profil_medical, name='profil_medical'),
]



# from django.urls import path
# from . import views

# urlpatterns = [
#     # Page d'accueil
#     path('', views.home, name='home'),
#
#     # Authentification
#     path('login/', views.custom_login, name='login'),  # ✅ CORRIGÉ
#     path('logout/', views.custom_logout, name='logout'),
#     path('inscription/', views.inscription, name='inscription'),
    
#     # Dashboards
#     path('dashboard/', views.dashboard, name='dashboard'),
#     path('dashboard/patient/', views.dashboard_patient, name='dashboard_patient'),
#     path('dashboard/medecin/', views.dashboard_medecin, name='dashboard_medecin'),
#     path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
#     path('dashboard/infirmier/', views.dashboard_infirmier, name='dashboard_infirmier'),
#     path('dashboard/secretaire/', views.dashboard_secretaire, name='dashboard_secretaire'),
    
#     # Rendez-vous
#     path('nouveau-rdv/', views.nouveau_rdv, name='nouveau_rdv'),
#     path('mes-rdv/', views.mes_rdv, name='mes_rdv'),
    
#     # Patients - Nouvelles URLs ajoutées
#     path('consultations/', views.consultations, name='consultations'),
#     path('mon-dossier-medical/', views.mon_dossier_medical, name='mon_dossier_medical'),
#     path('download-dossier-pdf/', views.download_my_dossier_pdf, name='download_my_dossier_pdf'),
#     path('nouvelle-consultation/', views.nouvelle_consultation, name='nouvelle_consultation'),
#     path('consultations-medecin/', views.consultations_medecin, name='consultations_medecin'),
#      # URLs médecin (AJOUTE CES LIGNES)
#     path('liste-patients/', views.liste_patients, name='liste_patients'),
#     path('consultations-medecin/', views.consultations_medecin, name='consultations_medecin'),
#     path('nouvelle-consultation/', views.nouvelle_consultation, name='nouvelle_consultation'),
#     path('rdv-medecin/', views.rdv_medecin, name='rdv_medecin'),
#     path('planning-medecin/', views.planning_medecin, name='planning_medecin'),
#     # Profil
#     path('profile/', views.profile, name='profile'),
# ]









# from django.urls import path
# from . import views
# from .admin import admin_site

# urlpatterns = [
#     # Pages publiques
#     path('', views.home, name='home'),
#     path('login/', views.login_view, name='login'),
#     path('inscription/', views.inscription, name='register'),
#     path('logout/', views.logout_view, name='logout'),
#     path('tous-rdv/', views.tous_les_rdv, name='tous_rdv'),
#      path('consultations/', views.consultations, name='consultations'),
#     path('mon-dossier-medical/', views.mon_dossier_medical, name='mon_dossier_medical'),
#     path('download-dossier-pdf/', views.download_my_dossier_pdf, name='download_my_dossier_pdf'),
#     path('dashboard/', views.dashboard, name='dashboard'),
#     path('mon-dossier-medical/', views.mon_dossier_medical, name='mon_dossier_medical'),
#     path('medecin/prescription/imprimer/<int:prescription_id>/', views.imprimer_prescription, name='imprimer_prescription'),
#     path('medecin/nouvelle-consultation/', views.nouvelle_consultation, name='nouvelle_consultation'),
#     path('dashboard/patient/', views.dashboard_patient, name='dashboard_patient'),
#     path('dashboard/medecin/', views.dashboard_medecin, name='dashboard_medecin'),
#     path('dashboard/infirmier/', views.dashboard_infirmier, name='dashboard_infirmier'),
#     path('dashboard/secretaire/', views.dashboard_secretaire, name='dashboard_secretaire'),
#     path('medecin/consultations/', views.mes_consultations_medecin, name='mes_consultations_medecin'),
#     path('medecin/patients/', views.liste_patients, name='liste_patients'),
#     path('medecin/prescription/', views.nouvelle_prescription, name='nouvelle_prescription'),
#     path('medecin/urgences/', views.urgences, name='urgences'),
#     path('mon-dossier-medical/pdf/', views.download_my_dossier_pdf, name='download_my_dossier_pdf'),
#     path('nouveau-rdv/', views.nouveau_rdv, name='nouveau_rdv'),
#     path('mes-rdv/', views.mes_rdv, name='mes_rdv'),
#     path('mes-consultations/', views.mes_consultations, name='mes_consultations'),
#     path('mon-dossier-medical/', views.mon_dossier_medical, name='mon_dossier_medical'),
#     path('mes-infos/', views.mes_infos, name='mes_infos'),
#     path('modifier-profil/', views.modifier_profil, name='modifier_profil'),
# ]
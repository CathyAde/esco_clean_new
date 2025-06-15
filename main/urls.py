from django.urls import path
from . import views
from .admin import admin_site

urlpatterns = [
    # Pages publiques
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('inscription/', views.inscription, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('tous-rdv/', views.tous_les_rdv, name='tous_rdv'),
    path('consultation/ajouter/<int:rdv_id>/', views.ajouter_consultation, name='ajouter_consultation'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('mon-dossier-medical/', views.mon_dossier_medical, name='mon_dossier_medical'),
    path('medecin/prescription/imprimer/<int:prescription_id>/', views.imprimer_prescription, name='imprimer_prescription'),
    path('medecin/nouvelle-consultation/', views.nouvelle_consultation, name='nouvelle_consultation'),
    path('dashboard/patient/', views.dashboard_patient, name='dashboard_patient'),
    path('dashboard/medecin/', views.dashboard_medecin, name='dashboard_medecin'),
    path('dashboard/infirmier/', views.dashboard_infirmier, name='dashboard_infirmier'),
    path('dashboard/secretaire/', views.dashboard_secretaire, name='dashboard_secretaire'),
    path('medecin/consultations/', views.consultations_medecin, name='consultations_medecin'),
    path('medecin/patients/', views.liste_patients, name='liste_patients'),
    path('medecin/prescription/', views.nouvelle_prescription, name='nouvelle_prescription'),
    path('medecin/urgences/', views.urgences, name='urgences'),
    path('mon-dossier-medical/pdf/', views.download_my_dossier_pdf, name='download_my_dossier_pdf'),
    path('nouveau-rdv/', views.nouveau_rdv, name='nouveau_rdv'),
    path('mes-rdv/', views.mes_rdv, name='mes_rdv'),
    path('mes-consultations/', views.consultations, name='consultations'),
    path('mon-dossier-medical/', views.mon_dossier_medical, name='mon_dossier_medical'),
    path('mes-infos/', views.mes_infos, name='mes_infos'),
    path('modifier-profil/', views.modifier_profil, name='modifier_profil'),
]


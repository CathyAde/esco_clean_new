from django.urls import path
from . import views
# Importer l'admin personnalisé
from .admin import admin_site

urlpatterns = [
    # Pages publiques
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('inscription/', views.inscription, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard principal avec redirection
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Dashboards par rôle
    path('dashboard/patient/', views.dashboard_patient, name='dashboard_patient'),
    path('dashboard/medecin/', views.dashboard_medecin, name='dashboard_medecin'),
    path('dashboard/infirmier/', views.dashboard_infirmier, name='dashboard_infirmier'),
    path('dashboard/secretaire/', views.dashboard_secretaire, name='dashboard_secretaire'),
    
    # Pages patients dédiées
    path('patient/nouveau-rdv/', views.nouveau_rdv, name='nouveau_rdv'),
    path('patient/mes-rdv/', views.mes_rdv, name='mes_rdv'),
    path('patient/mes-consultations/', views.mes_consultations, name='mes_consultations'),
    path('patient/mon-dossier-medical/', views.mon_dossier_medical, name='mon_dossier_medical'),
    path('patient/modifier-profil/', views.modifier_profil, name='modifier_profil'),
    path('patient/mes-infos/', views.mes_infos, name='mes_infos'),
     # Nouvelles URLs pour les actions rapides
    path('nouveau-rdv/', views.nouveau_rdv, name='nouveau_rdv'),
    path('mes-rdv/', views.mes_rdv, name='mes_rdv'),
    path('consultations/', views.consultations, name='consultations'),
    path('mon-dossier/', views.mon_dossier, name='mon_dossier'),
    # PDF exports
    path('admin/patient/<int:patient_id>/dossier-pdf/', views.download_dossier_pdf, name='download_dossier_pdf'),
    path('admin/consultation/<int:consultation_id>/ordonnance-pdf/', views.download_ordonnance_pdf, name='download_ordonnance_pdf'),
    path('patient/mon-dossier-pdf/', views.download_my_dossier_pdf, name='download_my_dossier_pdf'),
]




# from django.urls import path
# from . import views
# # Importer correctement l'admin personnalisé
# from .admin import admin_site

# urlpatterns = [
#     # Pages publiques
#     path('', views.home, name='home'),
#     path('login/', views.login_view, name='login'),
#     path('inscription/', views.inscription, name='register'),
#     path('logout/', views.logout_view, name='logout'),
    
#     # Dashboard principal avec redirection
#     path('dashboard/', views.dashboard, name='dashboard'),
    
#     # Dashboards par rôle
#     path('dashboard/patient/', views.dashboard_patient, name='dashboard_patient'),
#     path('dashboard/medecin/', views.dashboard_medecin, name='dashboard_medecin'),
#     path('dashboard/infirmier/', views.dashboard_infirmier, name='dashboard_infirmier'),
#     path('dashboard/secretaire/', views.dashboard_secretaire, name='dashboard_secretaire'),
    
#     # Pages patients dédiées
#     path('patient/nouveau-rdv/', views.nouveau_rdv, name='nouveau_rdv'),
#     path('patient/mes-rdv/', views.mes_rdv, name='mes_rdv'),
#     path('patient/mes-consultations/', views.mes_consultations, name='mes_consultations'),
#     path('patient/mon-dossier-medical/', views.mon_dossier_medical, name='mon_dossier_medical'),
#     path('patient/modifier-profil/', views.modifier_profil, name='modifier_profil'),
#     path('patient/mes-infos/', views.mes_infos, name='mes_infos'),
    
#     # PDF exports
#     path('admin/patient/<int:patient_id>/dossier-pdf/', views.download_dossier_pdf, name='download_dossier_pdf'),
#     path('admin/consultation/<int:consultation_id>/ordonnance-pdf/', views.download_ordonnance_pdf, name='download_ordonnance_pdf'),
#     path('patient/mon-dossier-pdf/', views.download_my_dossier_pdf, name='download_my_dossier_pdf'),
# ]








# # from django.urls import path, include
# # from django.contrib import admin
# # from . import views
# # from .admin import admin_site  # Importer notre admin personnalisé

# # urlpatterns = [
# #     # Pages publiques
# #     path('', views.home, name='home'),
# #     path('login/', views.login_view, name='login'),
# #     path('inscription/', views.inscription, name='register'),
# #     path('logout/', views.logout_view, name='logout'),
    
# #     # Dashboard principal avec redirection
# #     path('dashboard/', views.dashboard, name='dashboard'),
    
# #     # Dashboards par rôle (sauf admin qui utilise Django Admin)
# #     path('dashboard/patient/', views.dashboard_patient, name='dashboard_patient'),
# #     path('dashboard/medecin/', views.dashboard_medecin, name='dashboard_medecin'),
# #     path('dashboard/infirmier/', views.dashboard_infirmier, name='dashboard_infirmier'),
# #     path('dashboard/secretaire/', views.dashboard_secretaire, name='dashboard_secretaire'),
    
# #     # ===== NOUVELLES PAGES PATIENTS DÉDIÉES =====
# #     path('patient/nouveau-rdv/', views.nouveau_rdv, name='nouveau_rdv'),
# #     path('patient/mes-rdv/', views.mes_rdv, name='mes_rdv'),
# #     path('patient/mes-consultations/', views.mes_consultations, name='mes_consultations'),
# #     path('patient/mon-dossier-medical/', views.mon_dossier_medical, name='mon_dossier_medical'),
# #     path('patient/modifier-profil/', views.modifier_profil, name='modifier_profil'),
# #     path('patient/mes-infos/', views.mes_infos, name='mes_infos'),
    
# #     # ===== PDF EXPORTS =====
# #     path('admin/patient/<int:patient_id>/dossier-pdf/', views.download_dossier_pdf, name='download_dossier_pdf'),
# #     path('admin/consultation/<int:consultation_id>/ordonnance-pdf/', views.download_ordonnance_pdf, name='download_ordonnance_pdf'),
# #     path('patient/mon-dossier-pdf/', views.download_my_dossier_pdf, name='download_my_dossier_pdf'),
# # ]
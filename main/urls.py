from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('inscription/', views.inscription, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/patient/', views.dashboard_patient, name='dashboard_patient'),
    path('dashboard/medecin/', views.dashboard_medecin, name='dashboard_medecin'),
    path('dashboard/infirmier/', views.dashboard_infirmier, name='dashboard_infirmier'),
    path('dashboard/secretaire/', views.dashboard_secretaire, name='dashboard_secretaire'),
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),    
    path('admin/patient/<int:patient_id>/dossier-pdf/', views.download_dossier_pdf, name='download_dossier_pdf'),
    path('admin/consultation/<int:consultation_id>/ordonnance-pdf/', views.download_ordonnance_pdf, name='download_ordonnance_pdf'),
    path('mon-dossier-pdf/', views.download_my_dossier_pdf, name='download_my_dossier_pdf'),
]
 
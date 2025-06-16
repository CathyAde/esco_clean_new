from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse, Http404
from django.core.exceptions import PermissionDenied
from datetime import datetime, timedelta
from django.db.models.functions import TruncDate
from django.core.paginator import Paginator
import io
from datetime import datetime
# Imports des modèles et formulaires
from .models import CustomUser, Patient, Prescription, RendezVous, SoinsInfirmier, Consultation, Medecin, Infirmier, Secretaire
from .forms import CustomUserCreationForm, ProfilMedicalForm, RendezVousForm, ProfileUpdateForm

# Imports pour PDF
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
import datetime
from datetime import datetime, time
from django.utils.timezone import make_aware, is_naive
# Dans views.py - CORRECT ✅
from .models import Consultation, RendezVous, CustomUser

# ==================== DÉCORATEURS ====================

def patient_required(view_func):
    """Décorateur pour restreindre l'accès aux patients uniquement"""
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if hasattr(request.user, 'role') and request.user.role == 'patient':
            return view_func(request, *args, **kwargs)
        
        messages.error(request, 'Accès réservé aux patients.')
        return redirect('dashboard')
    return _wrapped_view

# Dans views.py, ajoute :

@login_required
def profil_medical(request):
    """Vue pour modifier le profil médical du patient"""
    if not (hasattr(request.user, 'role') and request.user.role == 'patient'):
        messages.error(request, 'Accès réservé aux patients.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ProfilMedicalForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user.profil_complete = True
            user.derniere_maj_profil = timezone.now()
            user.save()
            
            messages.success(request, 'Votre profil médical a été mis à jour avec succès!')
            return redirect('dashboard_patient')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = ProfilMedicalForm(instance=request.user)
    
    context = {
        'form': form,
        'user': request.user,
    }
    
    return render(request, 'profil_medical.html', context)

def medecin_ou_admin_required(view_func):
    """Décorateur pour médecins et admins"""
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        user_role = getattr(request.user, 'role', None)
        if user_role == 'docteur' or request.user.is_superuser or user_role == 'administrateur':
            return view_func(request, *args, **kwargs)
        
        raise PermissionDenied(f"Vous n'avez pas les permissions pour accéder à cette page. Votre rôle: {user_role}")
    return _wrapped_view

# ==================== VUES PRINCIPALES ====================

def home(request):
    """Page d'accueil"""
    return render(request, 'home.html')

def custom_login(request):
    """Vue de connexion personnalisée"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Bonjour {user.get_full_name() or user.username}!')
                
                # Redirection selon le rôle
                if hasattr(user, 'role'):
                    if user.role == 'patient':
                        return redirect('dashboard_patient')
                    elif user.role == 'docteur':
                        return redirect('dashboard_medecin')
                    elif user.role == 'administrateur':
                        return redirect('dashboard_admin')
                    elif user.role == 'infirmier':
                        return redirect('dashboard_infirmier')
                    elif user.role == 'secretaire':
                        return redirect('dashboard_secretaire')
                
                return redirect('dashboard')
            else:
                messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
        else:
            messages.error(request, 'Erreur dans le formulaire.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {'form': form})

def custom_logout(request):
    """Vue de déconnexion"""
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('home')

def inscription(request):
    """Vue d'inscription"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Compte créé avec succès! Vous pouvez maintenant vous connecter.')
            return redirect('login')
        else:
            messages.error(request, 'Erreur lors de la création du compte.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'inscription.html', {'form': form})

@login_required
def dashboard(request):
    """Dashboard général - redirige selon le rôle"""
    if hasattr(request.user, 'role'):
        if request.user.role == 'patient':
            return redirect('dashboard_patient')
        elif request.user.role == 'docteur':
            return redirect('dashboard_medecin')
        elif request.user.role == 'administrateur':
            return redirect('dashboard_admin')
        elif request.user.role == 'infirmier':
            return redirect('dashboard_infirmier')
        elif request.user.role == 'secretaire':
            return redirect('dashboard_secretaire')
    
    return render(request, 'dashboard.html')

# ==================== DASHBOARDS ====================

@login_required
def dashboard_patient(request):
    """Dashboard pour les patients"""
    if not (hasattr(request.user, 'role') and request.user.role == 'patient'):
        messages.error(request, 'Accès réservé aux patients.')
        return redirect('dashboard')
    
    # Récupérer les données du patient
    prochains_rdv = RendezVous.objects.filter(
        patient=request.user,
        date_rdv__gte=timezone.now().date()
    ).order_by('date_rdv')
    
    rdv_total = RendezVous.objects.filter(patient=request.user).count()
    consultations_total = Consultation.objects.filter(rdv__patient=request.user).count()
    
    dernieres_consultations = Consultation.objects.filter(
        rdv__patient=request.user
    ).order_by('-created_at')[:3]
    
    context = {
        'prochains_rdv': prochains_rdv[:5],
        'prochains_rdv_count': prochains_rdv.count(),
        'rdv_total': rdv_total,
        'consultations_total': consultations_total,
        'dernieres_consultations': dernieres_consultations,
    }
    
    return render(request, 'dashboard_patient.html', context)

@login_required
def dashboard_medecin(request):
    """Dashboard pour les médecins"""
    if not (hasattr(request.user, 'role') and request.user.role == 'docteur'):
        messages.error(request, 'Accès réservé aux médecins.')
        return redirect('dashboard')
    
    # Données aujourd'hui
    today = timezone.now().date()
    rdv_aujourd_hui = RendezVous.objects.filter(
        medecin=request.user,
        date_rdv=today
    ).order_by('heure_rdv')
    
    # Statistiques générales
    stats = {
        'rdv_total': RendezVous.objects.filter(medecin=request.user).count(),
        'rdv_aujourd_hui': rdv_aujourd_hui.count(),
        'patients_total': RendezVous.objects.filter(
            medecin=request.user
        ).values('patient').distinct().count(),
        'consultations_total': Consultation.objects.filter(
            rdv__medecin=request.user
        ).count(),
        'consultations_mois': Consultation.objects.filter(
            rdv__medecin=request.user,
            created_at__month=today.month,
            created_at__year=today.year
        ).count(),
    }
    
    # Prochains RDV (5 prochains)
    prochains_rdv = RendezVous.objects.filter(
        medecin=request.user,
        date_rdv__gte=today,
        status__in=['programme', 'confirme']
    ).order_by('date_rdv', 'heure_rdv')[:5]
    
    # Dernières consultations
    dernieres_consultations = Consultation.objects.filter(
        rdv__medecin=request.user
    ).order_by('-created_at')[:3]
    
    context = {
        'rdv_aujourd_hui': rdv_aujourd_hui,
        'prochains_rdv': prochains_rdv,
        'dernieres_consultations': dernieres_consultations,
        'stats': stats,
        'today': today,
        # Variables pour compatibilité template
        'rdv_count': stats['rdv_aujourd_hui'],
        'rdv_total': stats['rdv_total'],
        'patients_total': stats['patients_total'],
        'consultations_mois': stats['consultations_mois'],
    }
    
    return render(request, 'dashboard_medecin.html', context)

@login_required
def dashboard_admin(request):
    """Dashboard pour les administrateurs"""
    if not (request.user.is_superuser or (hasattr(request.user, 'role') and request.user.role == 'administrateur')):
        messages.error(request, 'Accès réservé aux administrateurs.')
        return redirect('dashboard')
    
    return render(request, 'dashboard_admin.html')

@login_required
def dashboard_infirmier(request):
    """Dashboard pour les infirmiers"""
    if not (hasattr(request.user, 'role') and request.user.role == 'infirmier'):
        messages.error(request, 'Accès réservé aux infirmiers.')
        return redirect('dashboard')
    
    return render(request, 'dashboard_infirmier.html')

@login_required
def dashboard_secretaire(request):
    """Dashboard pour les secrétaires"""
    if not (hasattr(request.user, 'role') and request.user.role == 'secretaire'):
        messages.error(request, 'Accès réservé aux secrétaires.')
        return redirect('dashboard')
    
    return render(request, 'dashboard_secretaire.html')

# ==================== RENDEZ-VOUS ====================

@login_required
def nouveau_rdv(request):
    """Vue pour créer un nouveau rendez-vous - POUR TOUS LES RÔLES"""
    user_role = getattr(request.user, 'role', None)
    
    # 🔧 AUTORISER patients, médecins et admins
    if not (user_role in ['patient', 'docteur'] or request.user.is_superuser):
        messages.error(request, f"Accès refusé. Votre rôle: {user_role}")
        return redirect('dashboard')
    
    medecins = CustomUser.objects.filter(role='docteur', is_active=True)
    patients = CustomUser.objects.filter(role='patient', is_active=True)
    
    if request.method == 'POST':
        form = RendezVousForm(request.POST, medecins=medecins)
        if form.is_valid():
            try:
                rdv = form.save(commit=False)
                
                # 🔧 Auto-assignation selon le rôle
                if user_role == 'patient':
                    rdv.patient = request.user
                    # Le médecin est choisi dans le formulaire
                elif user_role == 'docteur':
                    rdv.medecin = request.user
                    # Le patient est choisi dans le formulaire
                
                rdv.save()
                messages.success(request, 'Rendez-vous créé avec succès!')
                
                # Redirection selon le rôle
                if user_role == 'patient':
                    return redirect('dashboard_patient')
                else:
                    return redirect('dashboard_medecin')
                    
            except Exception as e:
                messages.error(request, f'Erreur: {str(e)}')
        else:
            messages.error(request, 'Erreurs dans le formulaire.')
    else:
        form = RendezVousForm(medecins=medecins)
        
        # 🔧 Configuration selon le rôle
        if user_role == 'patient':
            # Patient : masquer le champ patient, montrer médecins
            form.fields['patient'].widget = forms.HiddenInput()
            form.fields['patient'].initial = request.user
        elif user_role == 'docteur':
            # Médecin : masquer le champ médecin, montrer patients
            form.fields['medecin'].widget = forms.HiddenInput()
            form.fields['medecin'].initial = request.user
    
    return render(request, 'nouveau_rdv.html', {
        'form': form,
        'user_role': user_role,
        'medecins': medecins,
        'patients': patients
    })

@login_required
def mes_rdv(request):
    """Vue pour voir mes rendez-vous"""
    if hasattr(request.user, 'role') and request.user.role == 'patient':
        rdv_list = RendezVous.objects.filter(patient=request.user).order_by('-date_rdv')
    elif hasattr(request.user, 'role') and request.user.role == 'docteur':
        rdv_list = RendezVous.objects.filter(medecin=request.user).order_by('-date_rdv')
    else:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    return render(request, 'mes_rdv.html', {'rdv_list': rdv_list})

# ==================== VUES PATIENTS ====================

@patient_required
def consultations(request):
    """Vue pour afficher les consultations d'un patient"""
    consultations_list = Consultation.objects.filter(
        rdv__patient=request.user
    ).select_related('rdv__medecin').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(consultations_list, 10)
    page_number = request.GET.get('page')
    consultations_page = paginator.get_page(page_number)
    
    context = {
        'consultations_list': consultations_page,
        'total_consultations': consultations_list.count(),
    }
    
    return render(request, 'consultations.html', context)

@login_required
def mon_dossier_medical(request):
    """Vue pour afficher le dossier médical complet du patient"""
    if not (hasattr(request.user, 'role') and request.user.role == 'patient'):
        messages.error(request, 'Accès réservé aux patients.')
        return redirect('dashboard')
    
    # Récupérer toutes les données du patient
    rdv_list = RendezVous.objects.filter(patient=request.user).order_by('-date_rdv')[:10]
    
    consultations_list = Consultation.objects.filter(
        rdv__patient=request.user
    ).order_by('-created_at')[:5]
    
    prescriptions_list = Prescription.objects.filter(
        patient=request.user
    ).order_by('-date_prescription')[:5]
    
    # Statistiques
    stats = {
        'total_rdv': RendezVous.objects.filter(patient=request.user).count(),
        'total_consultations': Consultation.objects.filter(rdv__patient=request.user).count(),
        'total_prescriptions': Prescription.objects.filter(patient=request.user).count(),
        'prochains_rdv': RendezVous.objects.filter(
            patient=request.user,
            date_rdv__gte=timezone.now().date()
        ).count(),
    }
    
    # Profil médical (s'il existe)
    patient_profile = request.user if hasattr(request.user, 'profil_complete') else None
    
    context = {
        'rdv_list': rdv_list,
        'consultations_list': consultations_list,
        'prescriptions_list': prescriptions_list,
        'stats': stats,
        'patient_profile': patient_profile,
    }
    
    return render(request, 'mon_dossier_medical.html', context)
# Modifie la vue dossier_patient existante :

@login_required
def dossier_patient(request, patient_id):
    """Vue pour afficher le dossier médical complet d'un patient"""
    if not (hasattr(request.user, 'role') and request.user.role == 'docteur'):
        messages.error(request, 'Accès réservé aux médecins.')
        return redirect('dashboard')
    
    try:
        patient = CustomUser.objects.get(id=patient_id, role='patient')
    except CustomUser.DoesNotExist:
        messages.error(request, 'Patient non trouvé.')
        return redirect('liste_patients')
    
    # Historique des RDV avec ce médecin
    rdv_list = RendezVous.objects.filter(
        patient=patient,
        medecin=request.user
    ).order_by('-date_rdv', '-heure_rdv')
    
    # Consultations
    consultations_list = Consultation.objects.filter(
        rdv__patient=patient,
        rdv__medecin=request.user
    ).order_by('-created_at')
    
    # Prescriptions
    prescriptions_list = Prescription.objects.filter(
        patient=patient,
        medecin=request.user
    ).order_by('-date_prescription')
    
    # Statistiques
    stats = {
        'total_rdv': rdv_list.count(),
        'total_consultations': consultations_list.count(),
        'total_prescriptions': prescriptions_list.count(),
        'premier_rdv': rdv_list.last(),
        'dernier_rdv': rdv_list.first(),
    }
    
    # 🆕 Données médicales du patient
    donnees_medicales = {
        'age': patient.get_age(),
        'imc': patient.get_imc(),
        'tension': patient.get_tension(),
        'profil_complete': patient.profil_complete,
    }
    
    context = {
        'patient': patient,
        'rdv_list': rdv_list[:10],
        'consultations_list': consultations_list[:5],
        'prescriptions_list': prescriptions_list[:5],
        'stats': stats,
        'donnees_medicales': donnees_medicales,  # 🆕
    }
    
    return render(request, 'dossier_patient.html', context)


@login_required
def profile(request):
    """Vue pour modifier le profil"""
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil mis à jour avec succès!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    return render(request, 'profile.html', {'form': form})

@login_required
def nouvelle_consultation(request):
    """Vue pour créer une nouvelle consultation"""
    if not (hasattr(request.user, 'role') and request.user.role == 'docteur'):
        messages.error(request, 'Accès réservé aux médecins.')
        return redirect('dashboard')
    
    # 🔧 Récupérer les RDV du médecin qui n'ont pas encore de consultation
    rdv_sans_consultation = RendezVous.objects.filter(
        medecin=request.user,
        consultation__isnull=True  # RDV sans consultation associée
    ).order_by('-date_rdv', '-heure_rdv')
    
    if request.method == 'POST':
        rdv_id = request.POST.get('rdv_id')
        symptomes = request.POST.get('symptomes')
        diagnostic = request.POST.get('diagnostic')
        traitement = request.POST.get('traitement')
        observations = request.POST.get('observations')
        
        try:
            rdv = RendezVous.objects.get(id=rdv_id, medecin=request.user)
            
            # Vérifier qu'il n'y a pas déjà une consultation pour ce RDV
            if hasattr(rdv, 'consultation'):
                messages.error(request, 'Une consultation existe déjà pour ce rendez-vous.')
                return redirect('consultations_medecin')
            
            consultation = Consultation.objects.create(
                rdv=rdv,
                symptomes=symptomes,
                diagnostic=diagnostic,
                traitement=traitement,
                observations=observations
            )
            
            # Marquer le RDV comme terminé
            rdv.status = 'termine'
            rdv.save()
            
            messages.success(request, f'Consultation enregistrée pour {rdv.patient.get_full_name()}')
            return redirect('consultations_medecin')
            
        except RendezVous.DoesNotExist:
            messages.error(request, 'Rendez-vous non trouvé')
        except Exception as e:
            messages.error(request, f'Erreur: {str(e)}')
    
    context = {
        'rdv_list': rdv_sans_consultation,
        'rdv_count': rdv_sans_consultation.count()
    }
    
    return render(request, 'nouvelle_consultation.html', context)
@login_required
def liste_patients(request):
    """Vue pour afficher la liste des patients d'un médecin"""
    if not (hasattr(request.user, 'role') and request.user.role == 'docteur'):
        messages.error(request, 'Accès réservé aux médecins.')
        return redirect('dashboard')
    
    # 🔧 TOUS LES PATIENTS du système (pour que le médecin puisse les voir)
    tous_patients = CustomUser.objects.filter(
        role='patient',
        is_active=True
    ).order_by('last_name', 'first_name')
    
    # Créer les statistiques pour chaque patient
    patients_with_stats = []
    for patient in tous_patients:
        # RDV avec ce médecin
        rdv_count = RendezVous.objects.filter(
            patient=patient,
            medecin=request.user
        ).count()
        
        # Dernière consultation
        derniere_consultation = Consultation.objects.filter(
            rdv__patient=patient,
            rdv__medecin=request.user
        ).order_by('-created_at').first()
        
        # Dernière prescription
        derniere_prescription = Prescription.objects.filter(
            patient=patient,
            medecin=request.user
        ).order_by('-date_prescription').first()
        
        # Prochain RDV
        prochain_rdv = RendezVous.objects.filter(
            patient=patient,
            medecin=request.user,
            date_rdv__gte=timezone.now().date()
        ).order_by('date_rdv', 'heure_rdv').first()
        
        patients_with_stats.append({
            'patient': patient,
            'rdv_count': rdv_count,
            'derniere_consultation': derniere_consultation,
            'derniere_prescription': derniere_prescription,
            'prochain_rdv': prochain_rdv,
            'has_history': rdv_count > 0,  # Si le patient a un historique avec ce médecin
        })
    
    # Filtrer si demandé (seulement patients avec historique)
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'avec_historique':
        patients_with_stats = [p for p in patients_with_stats if p['has_history']]
    
    context = {
        'patients_with_stats': patients_with_stats,
        'total_patients': len(patients_with_stats),
        'filter_type': filter_type,
    }
    
    return render(request, 'liste_patients.html', context)
@login_required
def rdv_medecin(request):
    """Vue pour afficher les rendez-vous du médecin"""
    if not (hasattr(request.user, 'role') and request.user.role == 'docteur'):
        messages.error(request, 'Accès réservé aux médecins.')
        return redirect('dashboard')
    
    # Filtres
    filter_status = request.GET.get('status', 'all')
    filter_date = request.GET.get('date', 'all')
    
    # Base queryset
    rdv_queryset = RendezVous.objects.filter(medecin=request.user)
    
    # Appliquer les filtres
    if filter_status != 'all':
        rdv_queryset = rdv_queryset.filter(status=filter_status)
    
    if filter_date == 'today':
        rdv_queryset = rdv_queryset.filter(date_rdv=timezone.now().date())
    elif filter_date == 'week':
        start_week = timezone.now().date()
        end_week = start_week + timedelta(days=7)
        rdv_queryset = rdv_queryset.filter(date_rdv__range=[start_week, end_week])
    
    rdv_list = rdv_queryset.order_by('-date_rdv', '-heure_rdv')
    
    # Statistiques
    stats = {
        'total': rdv_queryset.count(),
        'today': RendezVous.objects.filter(
            medecin=request.user, 
            date_rdv=timezone.now().date()
        ).count(),
        'programme': rdv_queryset.filter(status='programme').count(),
        'termine': rdv_queryset.filter(status='termine').count(),
    }
    
    context = {
        'rdv_list': rdv_list,
        'stats': stats,
        'filter_status': filter_status,
        'filter_date': filter_date,
        'status_choices': RendezVous.STATUS_CHOICES,
    }
    
    return render(request, 'rdv_medecin.html', context)
@login_required
def planning_medecin(request):
    """Vue pour afficher le planning d'un médecin"""
    if not (hasattr(request.user, 'role') and request.user.role == 'docteur'):
        messages.error(request, 'Accès réservé aux médecins.')
        return redirect('dashboard')
    
    # Récupérer les RDV pour les 7 prochains jours
    today = timezone.now().date()
    end_date = today + timedelta(days=7)
    
    rdv_semaine = RendezVous.objects.filter(
        medecin=request.user,
        date_rdv__range=[today, end_date]
    ).select_related('patient').order_by('date_rdv', 'heure_rdv')
    
    # Organiser par jour
    planning_par_jour = {}
    for i in range(7):
        date = today + timedelta(days=i)
        planning_par_jour[date] = rdv_semaine.filter(date_rdv=date)
    
    context = {
        'planning_par_jour': planning_par_jour,
        'today': today,
    }
    
    return render(request, 'planning_medecin.html', context)

@login_required
def consultations_medecin(request):
    """Vue pour afficher les consultations d'un médecin"""
    if not (hasattr(request.user, 'role') and request.user.role == 'docteur'):
        messages.error(request, 'Accès réservé aux médecins.')
        return redirect('dashboard')
    
    # Récupérer toutes les consultations du médecin
    consultations_list = Consultation.objects.filter(
        rdv__medecin=request.user
    ).select_related('rdv__patient').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(consultations_list, 15)
    page_number = request.GET.get('page')
    consultations_page = paginator.get_page(page_number)
    
    context = {
        'consultations_list': consultations_page,
        'total_consultations': consultations_list.count(),
    }
    
    return render(request, 'consultations_medecin.html', context)

@login_required
def mes_prescriptions(request):
    """Vue pour afficher les prescriptions du médecin"""
    if not (hasattr(request.user, 'role') and request.user.role == 'docteur'):
        messages.error(request, 'Accès réservé aux médecins.')
        return redirect('dashboard')
    
    # Filtres
    patient_filter = request.GET.get('patient', '')
    date_filter = request.GET.get('date', 'all')
    
    # Base queryset
    prescriptions_queryset = Prescription.objects.filter(medecin=request.user)
    
    # Appliquer filtres
    if patient_filter:
        prescriptions_queryset = prescriptions_queryset.filter(
            patient__id=patient_filter
        )
    
    if date_filter == 'today':
        prescriptions_queryset = prescriptions_queryset.filter(
            date_prescription__date=timezone.now().date()
        )
    elif date_filter == 'week':
        start_week = timezone.now().date()
        end_week = start_week + timedelta(days=7)
        prescriptions_queryset = prescriptions_queryset.filter(
            date_prescription__date__range=[start_week, end_week]
        )
    elif date_filter == 'month':
        prescriptions_queryset = prescriptions_queryset.filter(
            date_prescription__month=timezone.now().month,
            date_prescription__year=timezone.now().year
        )
    
    prescriptions_list = prescriptions_queryset.order_by('-date_prescription')
    
    # Pagination
    paginator = Paginator(prescriptions_list, 10)
    page_number = request.GET.get('page')
    prescriptions_page = paginator.get_page(page_number)
    
    # Liste des patients pour le filtre
    patients_list = CustomUser.objects.filter(
        role='patient',
        prescriptions_patient__medecin=request.user
    ).distinct().order_by('first_name', 'last_name')
    
    context = {
        'prescriptions_list': prescriptions_page,
        'patients_list': patients_list,
        'patient_filter': patient_filter,
        'date_filter': date_filter,
        'total_prescriptions': prescriptions_queryset.count(),
    }
    
    return render(request, 'mes_prescriptions.html', context)
# Ajoute cette vue dans views.py après les autres vues médecin
# @login_required
# def nouvelle_prescription(request):
#     """Vue pour créer une nouvelle prescription"""
#     if not (hasattr(request.user, 'role') and request.user.role == 'docteur'):
#         messages.error(request, 'Accès réservé aux médecins.')
#         return redirect('dashboard')
    
#     if request.method == 'POST':
#         # Logique pour créer une prescription
#         patient_id = request.POST.get('patient_id')
#         medicaments = request.POST.get('medicaments')
#         instructions = request.POST.get('instructions', '')
        
#         try:
#             patient = CustomUser.objects.get(id=patient_id, role='patient')
            
#             prescription = Prescription.objects.create(
#                 patient=patient,
#                 medecin=request.user,
#                 contenu=f"Médicaments: {medicaments}\nInstructions: {instructions}",
#                 date_prescription=timezone.now()
#             )
            
#             messages.success(request, f'Prescription créée pour {patient.get_full_name()}')
#             return redirect('dashboard_medecin')
            
#         except CustomUser.DoesNotExist:
#             messages.error(request, 'Patient non trouvé')
#         except Exception as e:
#             messages.error(request, f'Erreur: {str(e)}')
    
#     # Récupérer les patients du médecin
#     patients = CustomUser.objects.filter(
#         role='patient',
#         rdv_patient__medecin=request.user
#     ).distinct()
    
#     return render(request, 'nouvelle_prescription.html', {
#         'patients': patients
#     })

@login_required
def nouvelle_prescription(request):
    """Vue pour créer une nouvelle prescription"""
    if not (hasattr(request.user, 'role') and request.user.role == 'docteur'):
        messages.error(request, 'Accès réservé aux médecins.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        patient_id = request.POST.get('patient_id')
        medicaments = request.POST.get('medicaments')
        instructions = request.POST.get('instructions', '')
        
        try:
            patient = CustomUser.objects.get(id=patient_id, role='patient')
            
            prescription = Prescription.objects.create(
                patient=patient,
                medecin=request.user,
                contenu=f"Médicaments: {medicaments}\nInstructions: {instructions}"
            )
            
            messages.success(request, f'Prescription créée pour {patient.get_full_name()}')
            return redirect('dashboard_medecin')
            
        except CustomUser.DoesNotExist:
            messages.error(request, 'Patient non trouvé')
        except Exception as e:
            messages.error(request, f'Erreur: {str(e)}')
    
    # 🔧 MODIFICATION ICI : Afficher TOUS les patients actifs
    patients = CustomUser.objects.filter(
        role='patient',
        is_active=True  # Tous les patients actifs, pas seulement ceux avec RDV
    ).order_by('first_name', 'last_name')
    
    return render(request, 'nouvelle_prescription.html', {
        'patients': patients
    })
    
 # Ajoute cette vue complète à la fin de views.py :

@login_required
def download_my_dossier_pdf(request):
    """Télécharger le dossier médical complet du patient en PDF"""
    if not (hasattr(request.user, 'role') and request.user.role == 'patient'):
        messages.error(request, 'Accès réservé aux patients.')
        return redirect('dashboard')
    
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from io import BytesIO
        
        # Créer le PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch)
        
        # Styles personnalisés
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=30,
            alignment=1,  # Center
            textColor=colors.purple,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=15,
            spaceBefore=20,
            textColor=colors.blue,
            fontName='Helvetica-Bold'
        )
        
        # Contenu du PDF
        story = []
        
        # En-tête avec logo virtuel
        story.append(Paragraph("🏥 ESCO - ESPACE SANTÉ FAMILLE", title_style))
        story.append(Paragraph("DOSSIER MÉDICAL PERSONNEL", title_style))
        story.append(Spacer(1, 20))
        
        # Informations personnelles
        story.append(Paragraph("👤 INFORMATIONS PERSONNELLES", heading_style))
        
        # Table des informations personnelles
        personal_data = [
            ['Nom complet:', request.user.get_full_name()],
            ['Email:', request.user.email],
            ['Téléphone:', request.user.telephone or 'Non renseigné'],
            ['Adresse:', request.user.adresse or 'Non renseignée'],
        ]
        
        if hasattr(request.user, 'date_naissance') and request.user.date_naissance:
            personal_data.append(['Date de naissance:', request.user.date_naissance.strftime('%d/%m/%Y')])
            if request.user.get_age():
                personal_data.append(['Âge:', f"{request.user.get_age()} ans"])
        
        personal_table = Table(personal_data, colWidths=[2.5*inch, 4*inch])
        personal_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(personal_table)
        story.append(Spacer(1, 20))
        
        # Données médicales
        if hasattr(request.user, 'poids') and (request.user.poids or request.user.taille or 
                                              getattr(request.user, 'groupe_sanguin', None) or 
                                              request.user.get_tension()):
            story.append(Paragraph("⚕️ DONNÉES MÉDICALES", heading_style))
            
            medical_data = []
            if request.user.poids:
                medical_data.append(['Poids:', f"{request.user.poids} kg"])
            if request.user.taille:
                medical_data.append(['Taille:', f"{request.user.taille} cm"])
            if request.user.get_imc():
                imc = request.user.get_imc()
                status_imc = ""
                if imc < 18.5:
                    status_imc = " (Insuffisance pondérale)"
                elif 18.5 <= imc < 25:
                    status_imc = " (Poids normal)"
                elif 25 <= imc < 30:
                    status_imc = " (Surpoids)"
                else:
                    status_imc = " (Obésité)"
                medical_data.append(['IMC:', f"{imc}{status_imc}"])
            
            if hasattr(request.user, 'groupe_sanguin') and request.user.groupe_sanguin:
                medical_data.append(['Groupe sanguin:', request.user.groupe_sanguin])
            if request.user.get_tension():
                tension = request.user.get_tension()
                systolique = request.user.tension_systolique
                status_tension = ""
                if systolique:
                    if systolique < 120:
                        status_tension = " (Normal)"
                    elif 120 <= systolique < 140:
                        status_tension = " (Élevé)"
                    else:
                        status_tension = " (Hypertension)"
                medical_data.append(['Tension artérielle:', f"{tension} mmHg{status_tension}"])
                
            if medical_data:
                medical_table = Table(medical_data, colWidths=[2.5*inch, 4*inch])
                medical_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgreen),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                story.append(medical_table)
                story.append(Spacer(1, 20))
        
        # Informations médicales détaillées
        if hasattr(request.user, 'allergies') and (request.user.allergies or 
                                                  getattr(request.user, 'antecedents_medicaux', None) or 
                                                  getattr(request.user, 'medicaments_actuels', None)):
            story.append(Paragraph("📋 INFORMATIONS MÉDICALES DÉTAILLÉES", heading_style))
            
            if request.user.allergies:
                story.append(Paragraph("<b>🚨 Allergies connues:</b>", styles['Normal']))
                story.append(Paragraph(request.user.allergies, styles['Normal']))
                story.append(Spacer(1, 10))
                
            if getattr(request.user, 'antecedents_medicaux', None):
                story.append(Paragraph("<b>📖 Antécédents médicaux:</b>", styles['Normal']))
                story.append(Paragraph(request.user.antecedents_medicaux, styles['Normal']))
                story.append(Spacer(1, 10))
                
            if getattr(request.user, 'medicaments_actuels', None):
                story.append(Paragraph("<b>💊 Médicaments actuels:</b>", styles['Normal']))
                story.append(Paragraph(request.user.medicaments_actuels, styles['Normal']))
                story.append(Spacer(1, 20))
        
        # Contact d'urgence
        if hasattr(request.user, 'personne_urgence_nom') and (request.user.personne_urgence_nom or 
                                                              getattr(request.user, 'personne_urgence_tel', None)):
            story.append(Paragraph("🆘 CONTACT D'URGENCE", heading_style))
            
            urgence_data = []
            if request.user.personne_urgence_nom:
                urgence_data.append(['Nom:', request.user.personne_urgence_nom])
            if getattr(request.user, 'personne_urgence_tel', None):
                urgence_data.append(['Téléphone:', request.user.personne_urgence_tel])
                
            if urgence_data:
                urgence_table = Table(urgence_data, colWidths=[2.5*inch, 4*inch])
                urgence_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.orange),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                story.append(urgence_table)
                story.append(Spacer(1, 20))
        
        # Historique des rendez-vous
        rdv_list = RendezVous.objects.filter(patient=request.user).order_by('-date_rdv')[:10]
        if rdv_list:
            story.append(Paragraph("📅 HISTORIQUE DES RENDEZ-VOUS (10 derniers)", heading_style))
            
            rdv_data = [['Date', 'Médecin', 'Motif', 'Statut']]
            for rdv in rdv_list:
                rdv_data.append([
                    rdv.date_rdv.strftime('%d/%m/%Y'),
                    rdv.medecin.get_full_name(),
                    (rdv.motif[:40] + '...') if len(rdv.motif) > 40 else rdv.motif,
                    rdv.get_status_display()
                ])
            
            rdv_table = Table(rdv_data, colWidths=[1.2*inch, 1.8*inch, 2.5*inch, 1*inch])
            rdv_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.purple),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(rdv_table)
            story.append(Spacer(1, 20))
        
        # Pied de page
        story.append(Spacer(1, 30))
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            alignment=1,  # Center
            textColor=colors.grey
        )
        
        story.append(Paragraph(f"📄 Document généré le {timezone.now().strftime('%d/%m/%Y à %H:%M')}", footer_style))
        story.append(Paragraph("🏥 ESCO - Espace Santé Famille - Confidentiel", footer_style))
        story.append(Paragraph("📞 Contact: contact@esco-sante.fr | ☎️ 01 23 45 67 89", footer_style))
        
        # Construire le PDF
        doc.build(story)
        
        # Préparer la réponse
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="dossier_medical_{request.user.username}_{timezone.now().strftime("%Y%m%d")}.pdf"'
        
        return response
        
    except ImportError:
        messages.error(request, 'Erreur: ReportLab non installé. Contactez l\'administrateur.')
        return redirect('dashboard_patient')
    except Exception as e:
        messages.error(request, f'Erreur lors de la génération du PDF: {str(e)}')
        return redirect('dashboard_patient')
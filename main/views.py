from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse, Http404
from django.core.exceptions import PermissionDenied
from .models import CustomUser, Patient, RendezVous, SoinsInfirmier, Consultation, Medecin, Infirmier, Secretaire
from .forms import CustomUserCreationForm, RendezVousForm, ProfileUpdateForm  # ✅ Imports corrects
from datetime import datetime, timedelta
import io


# Ajoutez ces nouvelles vues :

@login_required
def nouveau_rdv(request):
    """Vue pour créer un nouveau rendez-vous"""
    if request.method == 'POST':
        form = RendezVousForm(request.POST)
        if form.is_valid():
            rdv = form.save(commit=False)
            # Si c'est un patient connecté, l'associer automatiquement
            if request.user.role == 'patient':
                rdv.patient = request.user
            rdv.save()
            messages.success(request, 'Rendez-vous créé avec succès!')
            return redirect('dashboard_patient')
    else:
        form = RendezVousForm()
    
    return render(request, 'nouveau_rdv.html', {'form': form})

@login_required
def mes_rdv(request):
    """Vue pour voir les rendez-vous de l'utilisateur"""
    rdv_list = []
    
    # Si c'est un patient
    if request.user.role == 'patient':
        rdv_list = RendezVous.objects.filter(patient=request.user)
    # Si c'est un médecin
    elif request.user.role == 'docteur':
        rdv_list = RendezVous.objects.filter(medecin=request.user)
    
    context = {
        'rdv_list': rdv_list
    }
    return render(request, 'mes_rdv.html', context)

@login_required
def consultations(request):
    """Vue pour voir les consultations"""
    consultations_list = []
    
    # Si c'est un patient
    if request.user.role == 'patient':
        consultations_list = Consultation.objects.filter(rdv__patient=request.user)
    # Si c'est un médecin
    elif request.user.role == 'docteur':
        consultations_list = Consultation.objects.filter(rdv__medecin=request.user)
    
    context = {
        'consultations_list': consultations_list
    }
    return render(request, 'consultations.html', context)

@login_required
def mon_dossier(request):
    """Vue pour voir le dossier médical"""
    dossier_data = {}
    
    if request.user.role == 'patient':
        # Récupérer ou créer le profil patient
        patient, created = Patient.objects.get_or_create(user=request.user)
        dossier_data = {
            'patient': patient,
            'consultations': Consultation.objects.filter(rdv__patient=request.user)[:5],
            'rdv': RendezVous.objects.filter(patient=request.user)[:5]
        }
    
    return render(request, 'mon_dossier.html', dossier_data)
# ===== DÉCORATEURS PERSONNALISÉS =====

def role_required(allowed_roles):
    """Décorateur pour vérifier le rôle de l'utilisateur"""
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.role not in allowed_roles:
                raise PermissionDenied("Vous n'avez pas les permissions pour accéder à cette page.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

# ===== PAGES PUBLIQUES =====

def home(request):
    return render(request, 'home.html')

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Redirection selon le rôle
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                
                if user.role == 'patient':
                    return redirect('dashboard_patient')
                elif user.role == 'docteur':
                    return redirect('dashboard_medecin')
                elif user.role == 'infirmier':
                    return redirect('dashboard_infirmier')
                elif user.role == 'secretaire':
                    return redirect('dashboard_secretaire')
                elif user.is_staff or user.role == 'administrateur':
                    return redirect('/admin/')
                else:
                    return redirect('home')
            else:
                messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {'form': form})

def inscription(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                username = form.cleaned_data.get('username')
                role = form.cleaned_data.get('role')
                
                # Message de succès personnalisé selon le rôle
                role_messages = {
                    'patient': f'✅ Compte patient créé pour {username}! Votre ID patient est {user.user_id}.',
                    'docteur': f'✅ Compte médecin créé pour Dr. {username}! Votre ID médecin est {user.user_id}.',
                    'infirmier': f'✅ Compte infirmier créé pour {username}! Votre ID infirmier est {user.user_id}.',
                    'secretaire': f'✅ Compte secrétaire créé pour {username}! Votre ID secrétaire est {user.user_id}.',
                    'administrateur': f'✅ Compte administrateur créé pour {username}!'
                }
                
                message = role_messages.get(role, f'✅ Compte créé pour {username}!')
                messages.success(request, message)
                messages.info(request, '🔑 Vous pouvez maintenant vous connecter avec vos identifiants.')
                
                return redirect('login')
                
            except Exception as e:
                messages.error(request, f'❌ Erreur lors de la création du compte: {str(e)}')
                print(f"Erreur d'inscription: {e}")  # Pour le débogage
        else:
            # Afficher les erreurs du formulaire
            messages.error(request, '❌ Veuillez corriger les erreurs ci-dessous.')
            print(f"Erreurs du formulaire: {form.errors}")  # Pour le débogage
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'inscription.html', {'form': form})

# Redirection améliorée après connexion
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                
                # Messages de bienvenue personnalisés
                welcome_messages = {
                    'patient': f'Bienvenue {user.get_full_name() or user.username}! Accédez à votre espace patient.',
                    'docteur': f'Bienvenue Dr. {user.get_full_name() or user.username}! Votre espace médecin vous attend.',
                    'infirmier': f'Bienvenue {user.get_full_name() or user.username}! Consultez vos soins du jour.',
                    'secretaire': f'Bienvenue {user.get_full_name() or user.username}! Gérez les rendez-vous.',
                    'administrateur': f'Bienvenue Administrateur {user.username}! Accès complet au système.'
                }
                
                message = welcome_messages.get(user.role, f'Bienvenue {user.username}!')
                messages.success(request, message)
                
                # Redirection selon le rôle avec gestion des erreurs
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                
                try:
                    if user.role == 'patient':
                        return redirect('dashboard_patient')
                    elif user.role == 'docteur':
                        return redirect('dashboard_medecin')
                    elif user.role == 'infirmier':
                        return redirect('dashboard_infirmier')
                    elif user.role == 'secretaire':
                        return redirect('dashboard_secretaire')
                    elif user.is_staff or user.role == 'administrateur':
                        return redirect('/admin/')
                    else:
                        messages.warning(request, 'Rôle non reconnu, redirection vers l\'accueil.')
                        return redirect('home')
                except Exception as e:
                    messages.error(request, f'Erreur de redirection: {str(e)}')
                    return redirect('home')
            else:
                messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {'form': form})
def logout_view(request):
    logout(request)
    messages.info(request, 'Vous avez été déconnecté avec succès.')
    return redirect('home')

# ===== DASHBOARDS =====

@login_required
def dashboard(request):
    """Redirection automatique selon le rôle"""
    try:
        if request.user.is_staff or request.user.role == 'administrateur':
            return redirect('/admin/')
        elif request.user.role == 'docteur':
            return redirect('dashboard_medecin')
        elif request.user.role == 'infirmier':
            return redirect('dashboard_infirmier')
        elif request.user.role == 'secretaire':
            return redirect('dashboard_secretaire')
        elif request.user.role == 'patient':
            return redirect('dashboard_patient')
        else:
            messages.error(request, "Rôle utilisateur non reconnu.")
            return redirect('home')
    except Exception as e:
        messages.error(request, f"Erreur lors de la redirection: {str(e)}")
        return redirect('home')

@role_required(['patient'])
def dashboard_patient(request):
    try:
        # Récupérer ou créer le profil patient
        patient, created = Patient.objects.get_or_create(user=request.user)
        
        # Statistiques pour le patient
        rdv_futurs = RendezVous.objects.filter(
            patient=request.user, 
            date_rdv__gte=timezone.now()
        )
        
        rdv_passes = RendezVous.objects.filter(
            patient=request.user, 
            date_rdv__lt=timezone.now()
        )
        
        consultations = Consultation.objects.filter(
            rdv__patient=request.user
        )
        
        context = {
            'user': request.user,
            'patient': patient,
            'rdv_count': rdv_futurs.count(),
            'rdv_futurs': rdv_futurs[:5],  # 5 prochains RDV
            'rdv_passes': rdv_passes[:5],  # 5 derniers RDV
            'consultations_count': consultations.count(),
            'ordonnances_count': consultations.filter(traitement__isnull=False).count(),
        }
        return render(request, 'dashboard_patient.html', context)
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement du dashboard: {str(e)}")
        return redirect('home')

@role_required(['docteur'])
def dashboard_medecin(request):
    try:
        # Récupérer ou créer le profil médecin
        medecin, created = Medecin.objects.get_or_create(user=request.user)
        
        today = timezone.now().date()
        context = {
            'user': request.user,
            'medecin': medecin,
            'rdv_aujourdhui': RendezVous.objects.filter(
                medecin=request.user, 
                date_rdv__date=today
            ).count(),
            'patients_total': RendezVous.objects.filter(
                medecin=request.user
            ).values('patient').distinct().count(),
            'consultations_mois': Consultation.objects.filter(
                rdv__medecin=request.user,
                rdv__date_rdv__month=today.month
            ).count(),
        }
        return render(request, 'dashboard_medecin.html', context)
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement du dashboard: {str(e)}")
        return redirect('home')

@role_required(['infirmier'])
def dashboard_infirmier(request):
    try:
        # Récupérer ou créer le profil infirmier
        infirmier, created = Infirmier.objects.get_or_create(user=request.user)
        
        today = timezone.now().date()
        context = {
            'user': request.user,
            'infirmier': infirmier,
            'soins_aujourdhui': SoinsInfirmier.objects.filter(
                infirmier=request.user,
                date_soin__date=today
            ).count(),
            'patients_suivis': SoinsInfirmier.objects.filter(
                infirmier=request.user
            ).values('patient').distinct().count(),
        }
        return render(request, 'dashboard_infirmier.html', context)
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement du dashboard: {str(e)}")
        return redirect('home')

@role_required(['secretaire'])
def dashboard_secretaire(request):
    try:
        # Récupérer ou créer le profil secrétaire
        secretaire, created = Secretaire.objects.get_or_create(user=request.user)
        
        today = timezone.now().date()
        context = {
            'user': request.user,
            'secretaire': secretaire,
            'rdv_aujourdhui': RendezVous.objects.filter(
                date_rdv__date=today
            ).count(),
            'nouveaux_patients': Patient.objects.filter(
                created_at__date=today
            ).count(),
        }
        return render(request, 'dashboard_secretaire.html', context)
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement du dashboard: {str(e)}")
        return redirect('home')

# ===== PAGES PATIENTS =====

@role_required(['patient'])
def nouveau_rdv(request):
    if request.method == 'POST':
        try:
            medecin_id = request.POST.get('medecin')
            date_rdv = request.POST.get('date_rdv')
            heure_rdv = request.POST.get('heure_rdv')
            motif = request.POST.get('motif')
            
            if not all([medecin_id, date_rdv, heure_rdv, motif]):
                messages.error(request, 'Tous les champs sont obligatoires.')
                return redirect('nouveau_rdv')
            
            medecin = get_object_or_404(CustomUser, id=medecin_id, role='docteur')
            
            # Combiner date et heure
            datetime_str = f"{date_rdv} {heure_rdv}"
            date_rdv_complete = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
            
            # Vérifier si la date est dans le futur
            if date_rdv_complete <= timezone.now():
                messages.error(request, 'La date du rendez-vous doit être dans le futur.')
                return redirect('nouveau_rdv')
            
            # Créer le rendez-vous
            rdv = RendezVous.objects.create(
                patient=request.user,
                medecin=medecin,
                date_rdv=date_rdv_complete,
                motif=motif
            )
            
            messages.success(request, 'Votre rendez-vous a été programmé avec succès!')
            return redirect('mes_rdv')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création du rendez-vous: {str(e)}')
    
    context = {
        'medecins': CustomUser.objects.filter(role='docteur', is_active=True),
        'today': timezone.now().date(),
    }
    return render(request, 'nouveau_rdv.html', context)

@role_required(['patient'])
def mes_rdv(request):
    try:
        rdv_futurs = RendezVous.objects.filter(
            patient=request.user,
            date_rdv__gte=timezone.now()
        ).order_by('date_rdv')
        
        rdv_passes = RendezVous.objects.filter(
            patient=request.user,
            date_rdv__lt=timezone.now()
        ).order_by('-date_rdv')
        
        context = {
            'rdv_futurs': rdv_futurs,
            'rdv_passes': rdv_passes,
        }
        return render(request, 'mes_rdv.html', context)
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement des rendez-vous: {str(e)}")
        return redirect('dashboard_patient')

@role_required(['patient'])
def mes_consultations(request):
    try:
        consultations = Consultation.objects.filter(
            rdv__patient=request.user
        ).order_by('-rdv__date_rdv')
        
        context = {
            'consultations': consultations,
        }
        return render(request, 'mes_consultations.html', context)
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement des consultations: {str(e)}")
        return redirect('dashboard_patient')

@role_required(['patient'])
def mes_infos(request):
    try:
        patient = Patient.objects.filter(user=request.user).first()
        
        context = {
            'user': request.user,
            'patient': patient,
        }
        return render(request, 'mes_infos.html', context)
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement des informations: {str(e)}")
        return redirect('dashboard_patient')

@role_required(['patient'])
def modifier_profil(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Votre profil a été mis à jour avec succès!')
                return redirect('mes_infos')
            except Exception as e:
                messages.error(request, f'Erreur lors de la mise à jour: {str(e)}')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    context = {
        'form': form,
    }
    return render(request, 'modifier_profil.html', context)

# ===== FONCTIONS UTILITAIRES =====

@role_required(['patient'])
def mon_dossier_medical(request):
    try:
        patient = get_object_or_404(Patient, user=request.user)
        consultations = Consultation.objects.filter(rdv__patient=request.user)
        rdv_historique = RendezVous.objects.filter(patient=request.user).order_by('-date_rdv')
        
        context = {
            'patient': patient,
            'consultations': consultations,
            'rdv_historique': rdv_historique,
        }
        return render(request, 'mon_dossier_medical.html', context)
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement du dossier: {str(e)}")
        return redirect('dashboard_patient')

# Fonctions PDF (à implémenter selon vos besoins)
def download_dossier_pdf(request, patient_id):
    # Implémentation PDF
    return HttpResponse("PDF en cours de développement", content_type="text/plain")

def download_ordonnance_pdf(request, consultation_id):
    # Implémentation PDF
    return HttpResponse("PDF en cours de développement", content_type="text/plain")

def download_my_dossier_pdf(request):
    # Implémentation PDF
    return HttpResponse("PDF en cours de développement", content_type="text/plain") 
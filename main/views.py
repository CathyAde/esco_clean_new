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
import io
# Imports des modèles et formulaires
from .models import CustomUser, Patient, Prescription, RendezVous, SoinsInfirmier, Consultation, Medecin, Infirmier, Secretaire
from .forms import CustomUserCreationForm, RendezVousForm, ProfileUpdateForm
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



@login_required
def download_my_dossier_pdf(request):
    if request.user.role != 'patient':
        messages.error(request, 'Accès réservé aux patients.')
        return redirect('home')
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="dossier_medical_{request.user.username}_{datetime.date.today().strftime("%Y%m%d")}.pdf"'
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    story = []
    
    # Couleurs
    purple_color = HexColor('#7c3aed')
    
    # **HEADER AVEC LE NOM CORRECT DE LA CLINIQUE**
    header_style = ParagraphStyle(
        'ESCOHeader',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=5,
        textColor=purple_color,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    clinic_style = ParagraphStyle(
        'ClinicInfo',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=15,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    # Header corrigé avec le bon nom
    story.append(Paragraph("🏥 ESPACE SANTÉ FAMILLE", header_style))
    story.append(Paragraph("Centre Médical - Soins de Qualité Supérieure", clinic_style))
    story.append(Paragraph("📍 [Votre Adresse] | ☎️ [Votre Téléphone] | 🌐 www.espacesantefamille.com", clinic_style))
    story.append(Spacer(1, 20))
    
    # Ligne de séparation
    story.append(Paragraph("<hr/>", styles['Normal']))
    story.append(Spacer(1, 15))
    
    # Titre du document
    title_style = ParagraphStyle(
        'DocumentTitle',
        parent=styles['Heading2'],
        fontSize=18,
        spaceAfter=20,
        textColor=purple_color,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    story.append(Paragraph(f"DOSSIER MÉDICAL - {request.user.get_full_name().upper()}", title_style))
    
    # Informations patient complètes
    patient_info = [
        ["Informations Patient", ""],
        ["ID Patient:", request.user.user_id or "Non défini"],
        ["Nom complet:", request.user.get_full_name() or request.user.username],
        ["Email:", request.user.email or "Non renseigné"],
        ["Téléphone:", request.user.telephone or "Non renseigné"],
        ["Date de naissance:", request.user.date_naissance.strftime("%d/%m/%Y") if request.user.date_naissance else "Non renseignée"],
        ["Adresse:", request.user.adresse or "Non renseignée"],
    ]
    
    # Ajouter les informations du profil Patient si disponible
    try:
        patient_profile = Patient.objects.get(user=request.user)
        patient_info.extend([
            ["Groupe sanguin:", patient_profile.groupe_sanguin or "Non renseigné"],
            ["Profession:", patient_profile.profession or "Non renseignée"],
            ["Poids:", f"{patient_profile.poids} kg" if patient_profile.poids else "Non renseigné"],
            ["Taille:", f"{patient_profile.taille} cm" if patient_profile.taille else "Non renseignée"],
            ["Allergies:", patient_profile.allergies or "Aucune connue"],
            ["Antécédents:", patient_profile.antecedents or "Aucun"],
        ])
    except Patient.DoesNotExist:
        pass
    
    # Créer le tableau
    table = Table(patient_info, colWidths=[3*inch, 3*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), purple_color),
        ('TEXTCOLOR', (0, 0), (1, 0), HexColor('#ffffff')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#cccccc')),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Historique des rendez-vous
    rdv_list = RendezVous.objects.filter(patient=request.user).order_by('-date_rdv')
    if rdv_list.exists():
        story.append(Paragraph("HISTORIQUE DES RENDEZ-VOUS", styles['Heading3']))
        rdv_data = [["Date", "Médecin", "Motif", "Statut"]]
        for rdv in rdv_list[:10]:  # Limiter à 10 derniers RDV
            rdv_data.append([
                rdv.date_rdv.strftime("%d/%m/%Y"),
                f"Dr. {rdv.medecin.get_full_name()}" if rdv.medecin else "Non assigné",
                rdv.motif[:50] + "..." if len(rdv.motif) > 50 else rdv.motif,
                rdv.get_status_display() if hasattr(rdv, 'get_status_display') else "Programmé"
            ])
        
        rdv_table = Table(rdv_data, colWidths=[1.5*inch, 2*inch, 2*inch, 1.5*inch])
        rdv_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), purple_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#cccccc')),
        ]))
        story.append(rdv_table)
    
    # Footer
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=HexColor('#666666')
    )
    story.append(Paragraph(f"Document généré le {datetime.date.today().strftime('%d/%m/%Y')} - Espace Santé Famille", footer_style))
    
    # Construire le PDF
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response

# Décorateur personnalisé pour les permissions
def medecin_ou_admin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Permettre l'accès aux médecins et administrateurs
        if (hasattr(request.user, 'role') and request.user.role == 'docteur') or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        raise PermissionDenied("Vous n'avez pas les permissions pour accéder à cette page.")
    return _wrapped_view
# Appliquer le décorateur corrigé à la vue
# Décorateur personnalisé pour les permissions
def medecin_ou_admin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Debug - ajoutons quelques logs
        print(f"DEBUG - Utilisateur: {request.user.username}")
        print(f"DEBUG - Role: {getattr(request.user, 'role', 'Pas de rôle')}")
        print(f"DEBUG - Is superuser: {request.user.is_superuser}")
        
        # Permettre l'accès aux médecins et administrateurs
        user_role = getattr(request.user, 'role', None)
        if user_role == 'docteur' or request.user.is_superuser or user_role == 'administrateur':
            return view_func(request, *args, **kwargs)
        
        raise PermissionDenied(f"Vous n'avez pas les permissions pour accéder à cette page. Votre rôle: {user_role}")
    return _wrapped_view

# Appliquer le décorateur corrigé à la vue
@medecin_ou_admin_required
def nouveau_rdv(request):
    if request.method == 'POST':
        form = RendezVousForm(request.POST)
        if form.is_valid():
            rdv = form.save(commit=False)
            # Si c'est un médecin, l'assigner automatiquement
            if hasattr(request.user, 'role') and request.user.role == 'docteur':
                rdv.medecin = request.user
            rdv.save()
            messages.success(request, 'Rendez-vous ajouté avec succès!')
            return redirect('dashboard_medecin')  # Rediriger vers le dashboard médecin
        else:
            messages.error(request, 'Erreur lors de l\'ajout du rendez-vous.')
            print("Erreurs de formulaire:", form.errors)
    else:
        form = RendezVousForm()
        
        # Filtrer les choix selon le rôle
        if hasattr(request.user, 'role') and request.user.role == 'docteur':
            # Pour les médecins : pré-sélectionner le médecin et filtrer les patients
            form.fields['medecin'].queryset = CustomUser.objects.filter(id=request.user.id)
            form.fields['medecin'].initial = request.user
            form.fields['medecin'].widget.attrs['readonly'] = True
            
            # Tous les patients disponibles pour commencer
            form.fields['patient'].queryset = CustomUser.objects.filter(role='patient')
        else:
            # Pour les admins : tous les médecins et patients
            form.fields['medecin'].queryset = CustomUser.objects.filter(role='docteur')
            form.fields['patient'].queryset = CustomUser.objects.filter(role='patient')
    
    return render(request, 'main/nouveau_rdv.html', {'form': form})

@login_required
def nouveau_rdv(request):
    user_role = getattr(request.user, 'role', None)
    print(f"DEBUG - Role de l'utilisateur: {user_role}")
    
    # Autoriser patients, médecins et admins
    if not (user_role in ['patient', 'docteur'] or request.user.is_superuser):
        messages.error(request, f"Accès refusé. Votre rôle: {user_role}")
        return redirect('dashboard')
    
    # RÉCUPÉRER LES LISTES
    medecins = CustomUser.objects.filter(role='docteur', is_active=True)
    patients = CustomUser.objects.filter(role='patient', is_active=True)  # ⭐ AJOUTER ceci
    
    print(f"DEBUG - Nombre de médecins: {medecins.count()}")
    print(f"DEBUG - Nombre de patients: {patients.count()}")  # ⭐ Debug pour patients
    
    if request.method == 'POST':
        print("=== DONNÉES POST REÇUES ===")
        for key, value in request.POST.items():
            print(f"{key}: {value}")
        print("==========================")
        
        form = RendezVousForm(request.POST, medecins=medecins)  # Passer les médecins
        if form.is_valid():
            try:
                rdv = form.save(commit=False)
                
                # Auto-assignation selon le rôle
                if user_role == 'patient':
                    rdv.patient = request.user
                elif user_role == 'docteur':
                    rdv.medecin = request.user
                
                rdv.save()
                messages.success(request, 'Rendez-vous créé avec succès!')
                
                if user_role == 'patient':
                    return redirect('dashboard_patient')
                else:
                    return redirect('dashboard_medecin')
                    
            except Exception as e:
                messages.error(request, f'Erreur: {str(e)}')
                print(f"Erreur de sauvegarde: {e}")
        else:
            messages.error(request, 'Erreurs dans le formulaire.')
            print("Erreurs:", form.errors)
    else:
        form = RendezVousForm(medecins=medecins)
        
        # Configuration selon le rôle
        if user_role == 'patient':
            form.fields['patient'].queryset = CustomUser.objects.filter(id=request.user.id)
            form.fields['patient'].initial = request.user
            form.fields['patient'].widget = forms.HiddenInput()
            form.fields['medecin'].queryset = medecins
        elif user_role == 'docteur':
            form.fields['medecin'].queryset = CustomUser.objects.filter(id=request.user.id)
            form.fields['medecin'].initial = request.user
            form.fields['medecin'].widget = forms.HiddenInput()
            form.fields['patient'].queryset = patients  # ⭐ Utiliser la liste des patients
        else:
            # Pour les admins
            form.fields['medecin'].queryset = medecins
            form.fields['patient'].queryset = patients  # ⭐ Utiliser la liste des patients
    
    context = {
        'form': form,
        'user': request.user,
        'medecins': medecins,
        'patients': patients,  # ⭐ AJOUTER les patients au contexte
    }
    
    return render(request, 'main/nouveau_rdv.html', context)

@login_required
def mes_rdv(request):
    """Afficher tous les rendez-vous du patient (créés par admin ou patient)"""
    if request.user.role != 'patient':
        messages.error(request, 'Accès réservé aux patients.')
        return redirect('dashboard')
    
    # CORRECTION : Récupérer TOUS les RDV où l'utilisateur est patient
    rdv_list = RendezVous.objects.filter(patient=request.user).order_by('-date_rdv', '-heure_rdv')
    
    return render(request, 'main/mes_rdv.html', {
        'rdv_list': rdv_list,
        'user': request.user
    })

@login_required
def mes_consultations(request):
    """Vue pour voir l'historique des consultations"""
    if request.user.role != 'patient':
        messages.error(request, 'Accès réservé aux patients.')
        return redirect('home')
    
    try:
        consultations_list = Consultation.objects.filter(
            rdv__patient=request.user
        ).order_by('-rdv__date_rdv')
        
        context = {
            'consultations_list': consultations_list,
            'user': request.user
        }
        return render(request, 'consultations.html', context)
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement des consultations: {str(e)}")
        return redirect('dashboard_patient')

@login_required
def mon_dossier_medical(request):
    """Vue pour voir le dossier médical complet"""
    if request.user.role != 'patient':
        messages.error(request, 'Accès réservé aux patients.')
        return redirect('home')
    
    try:
        # Récupérer ou créer le profil patient
        patient, created = Patient.objects.get_or_create(user=request.user)
        
        # Récupérer toutes les données médicales
        rdv_list = RendezVous.objects.filter(patient=request.user).order_by('-date_rdv')
        consultations_list = Consultation.objects.filter(rdv__patient=request.user).order_by('-rdv__date_rdv')
        soins_list = SoinsInfirmier.objects.filter(patient=request.user).order_by('-date_soin')
        
        context = {
            'patient': patient,
            'rdv_list': rdv_list,
            'consultations_list': consultations_list,
            'soins_list': soins_list,
            'user': request.user
        }
        return render(request, 'mon_dossier.html', context)
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement du dossier: {str(e)}")
        return redirect('dashboard_patient')

@login_required
def mes_infos(request):
    """Vue pour voir les informations personnelles"""
    if request.user.role != 'patient':
        messages.error(request, 'Accès réservé aux patients.')
        return redirect('home')
    
    try:
        patient, created = Patient.objects.get_or_create(user=request.user)
        
        # Statistiques du patient
        stats = {
            'rdv_total': RendezVous.objects.filter(patient=request.user).count(),
            'rdv_futurs': RendezVous.objects.filter(
                patient=request.user, 
                date_rdv__gte=timezone.now().date()
            ).count(),
            'consultations_total': Consultation.objects.filter(rdv__patient=request.user).count(),
            'soins_total': SoinsInfirmier.objects.filter(patient=request.user).count(),
        }
        
        context = {
            'patient': patient,
            'user': request.user,
            'stats': stats
        }
        return render(request, 'mes_infos.html', context)
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement des informations: {str(e)}")
        return redirect('dashboard_patient')

@login_required
def modifier_profil(request):
    """Vue pour modifier le profil"""
    if request.user.role != 'patient':
        messages.error(request, 'Accès réservé aux patients.')
        return redirect('home')
    
    try:
        patient, created = Patient.objects.get_or_create(user=request.user)
        
        if request.method == 'POST':
            form = ProfileUpdateForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profil mis à jour avec succès!')
                return redirect('mes_infos')
            else:
                messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
        else:
            form = ProfileUpdateForm(instance=request.user)
        
        context = {
            'form': form,
            'patient': patient,
            'user': request.user
        }
        return render(request, 'modifier_profil.html', context)
    except Exception as e:
        messages.error(request, f"Erreur lors de la modification du profil: {str(e)}")
        return redirect('dashboard_patient')

# Alias pour compatibilité
consultations = mes_consultations
mon_dossier = mon_dossier_medical# ===== VUES PATIENTS COMPLÈTES =====

@login_required
def nouveau_rdv(request):
    """Vue pour créer un nouveau rendez-vous"""
    if request.user.role != 'patient':
        messages.error(request, 'Accès réservé aux patients.')
        return redirect('home')
    
    if request.method == 'POST':
        form = RendezVousForm(request.POST)
        if form.is_valid():
            rdv = form.save(commit=False)
            rdv.patient = request.user
            rdv.save()
            messages.success(request, 'Rendez-vous créé avec succès!')
            return redirect('mes_rdv')
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = RendezVousForm()
    
    return render(request, 'nouveau_rdv.html', {'form': form})

@login_required
def mes_rdv(request):
    """Vue pour voir les rendez-vous du patient"""
    if request.user.role != 'patient':
        messages.error(request, 'Accès réservé aux patients.')
        return redirect('home')
    
    try:
        rdv_list = RendezVous.objects.filter(patient=request.user).order_by('-date_rdv', '-heure_rdv')
        context = {
            'rdv_list': rdv_list,
            'user': request.user
        }
        return render(request, 'mes_rdv.html', context)
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement des rendez-vous: {str(e)}")
        return redirect('dashboard_patient')
@login_required
def mes_consultations_medecin(request):
    if not (hasattr(request.user, 'role') and request.user.role == 'docteur'):
        messages.error(request, 'Accès réservé aux médecins.')
        return redirect('dashboard')
    
    # Récupérer toutes les consultations du médecin
    consultations = Consultation.objects.filter(medecin=request.user).order_by('-date_consultation')
    
    # Récupérer les RDV avec consultations
    rdv_avec_consultations = RendezVous.objects.filter(
        medecin=request.user,
        # Optionnel : filtrer seulement les RDV qui ont des consultations
        # consultation__isnull=False
    ).order_by('-date_rdv')
    
    return render(request, 'mes_consultations_medecin.html', {
        'consultations_list': consultations,
        'rdv_list': rdv_avec_consultations,
    })
# @login_required
# def mes_consultations_medecin(request):
#     if request.user.role != 'docteur':
#         messages.error(request, 'Accès réservé aux médecins.')
#         return redirect('dashboard')
    
#     # CORRECTION : Récupérer les RDV du médecin avec leurs consultations
#     rdv_avec_consultations = RendezVous.objects.filter(
#         medecin=request.user
#     ).select_related('patient').prefetch_related('consultation_set').order_by('-date_rdv', '-heure_rdv')
    
#     # Ou si vous voulez seulement les consultations terminées :
#     consultations = Consultation.objects.filter(
#         rdv__medecin=request.user
#     ).select_related('rdv__patient', 'rdv__medecin').order_by('-created_at')
    
#     return render(request, 'mes_consultations_medecin.html', {
#         'rdv_list': rdv_avec_consultations,
#         'consultations_list': consultations  # Si vous voulez utiliser les consultations directement
#     })
@login_required
def liste_patients(request):
    if request.user.role != 'docteur':
        messages.error(request, 'Accès réservé aux médecins.')
        return redirect('dashboard')
    
    # CORRECTION : Récupérer les patients avec leurs RDV chez ce médecin
    patients_avec_rdv = CustomUser.objects.filter(
        role='patient',
        rdv_patient__medecin=request.user  # Patients qui ont des RDV avec ce médecin
    ).distinct().order_by('first_name', 'last_name')
    
    # OU si vous voulez tous les patients :
    # patients = CustomUser.objects.filter(role='patient', is_active=True).order_by('first_name', 'last_name')
    
    return render(request, 'liste_patients.html', {
        'patients': patients_avec_rdv
    })

@login_required
def nouvelle_prescription(request):
    """Créer une nouvelle prescription"""
    if request.user.role != 'docteur':
        messages.error(request, 'Accès réservé aux médecins.')
        return redirect('home')
    
    # Logique pour créer une prescription
    return render(request, 'nouvelle_prescription.html')

@login_required
def urgences(request):
    """Voir les patients en urgence"""
    if request.user.role != 'docteur':
        messages.error(request, 'Accès réservé aux médecins.')
        return redirect('home')
    
    # Patients prioritaires/urgents
    urgences = RendezVous.objects.filter(
        medecin=request.user,
        status='urgent'
    ).order_by('-date_rdv')
    
    context = {
        'urgences': urgences,
    }
    return render(request, 'urgences.html', context)

@login_required
def mon_dossier_medical(request):
    """Vue pour voir le dossier médical complet"""
    if request.user.role != 'patient':
        messages.error(request, 'Accès réservé aux patients.')
        return redirect('home')
    
    try:
        # Récupérer ou créer le profil patient
        patient, created = Patient.objects.get_or_create(user=request.user)
        
        # Récupérer toutes les données médicales
        rdv_list = RendezVous.objects.filter(patient=request.user).order_by('-date_rdv')
        consultations_list = Consultation.objects.filter(rdv__patient=request.user).order_by('-rdv__date_rdv')
        soins_list = SoinsInfirmier.objects.filter(patient=request.user).order_by('-date_soin')
        
        context = {
            'patient': patient,
            'rdv_list': rdv_list,
            'consultations_list': consultations_list,
            'soins_list': soins_list,
            'user': request.user
        }
        return render(request, 'mon_dossier.html', context)
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement du dossier: {str(e)}")
        return redirect('dashboard_patient')

@login_required
def mes_infos(request):
    """Vue pour voir les informations personnelles"""
    if request.user.role != 'patient':
        messages.error(request, 'Accès réservé aux patients.')
        return redirect('home')
    
    try:
        patient, created = Patient.objects.get_or_create(user=request.user)
        
        # Statistiques du patient
        stats = {
            'rdv_total': RendezVous.objects.filter(patient=request.user).count(),
            'rdv_futurs': RendezVous.objects.filter(
                patient=request.user, 
                date_rdv__gte=timezone.now().date()
            ).count(),
            'consultations_total': Consultation.objects.filter(rdv__patient=request.user).count(),
            'soins_total': SoinsInfirmier.objects.filter(patient=request.user).count(),
        }
        
        context = {
            'patient': patient,
            'user': request.user,
            'stats': stats
        }
        return render(request, 'mes_infos.html', context)
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement des informations: {str(e)}")
        return redirect('dashboard_patient')

@login_required
def modifier_profil(request):
    """Modifier le profil utilisateur avec informations médicales"""
    if request.user.role != 'patient':
        messages.error(request, 'Accès réservé aux patients.')
        return redirect('dashboard')
    
    # Récupérer ou créer le profil patient
    patient, created = Patient.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user, patient=patient)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre profil a été mis à jour avec succès!')
            return redirect('mon_dossier_medical')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = ProfileUpdateForm(instance=request.user, patient=patient)
    
    return render(request, 'main/modifier_profil.html', {
        'form': form,
        'patient': patient
    })
# Alias pour compatibilité
consultations = mes_consultations
mon_dossier = mon_dossier_medical


@login_required
def nouveau_rdv(request):
    """Créer un nouveau rendez-vous"""
    if request.user.role != 'patient':
        messages.error(request, 'Accès réservé aux patients.')
        return redirect('dashboard')
    if request.user.role not in ['docteur', 'medecin', 'doctor']:
        # Créer automatiquement le rôle si nécessaire
        if hasattr(request.user, 'role'):
            request.user.role = 'docteur'
            request.user.save()
    if request.method == 'POST':
        # Traitement manuel des données du formulaire
        medecin_id = request.POST.get('medecin')
        date_rdv = request.POST.get('date_rdv')
        heure_rdv = request.POST.get('heure_rdv')
        motif = request.POST.get('motif')
        
        # Validation
        errors = []
        if not medecin_id:
            errors.append('Veuillez sélectionner un médecin.')
        if not date_rdv:
            errors.append('Veuillez sélectionner une date.')
        if not heure_rdv:
            errors.append('Veuillez sélectionner une heure.')
        if not motif:
            errors.append('Veuillez saisir un motif.')
            
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            try:
                # Convertir les chaînes en objets datetime/time
                date_obj = datetime.strptime(date_rdv, '%Y-%m-%d').date()
                heure_obj = datetime.strptime(heure_rdv, '%H:%M').time()
                
                # Créer le rendez-vous
                medecin = CustomUser.objects.get(id=medecin_id, role='docteur')
                rdv = RendezVous.objects.create(
                    patient=request.user,
                    medecin=medecin,
                    date_rdv=date_obj,
                    heure_rdv=heure_obj,
                    motif=motif,
                    status='programme'
                )
                messages.success(request, 'Votre rendez-vous a été programmé avec succès!')
                return redirect('mes_rdv')
            except ValueError as e:
                messages.error(request, 'Format de date ou d\'heure incorrect.')
            except Exception as e:
                messages.error(request, f'Erreur lors de la création du rendez-vous: {str(e)}')

    # Récupérer tous les médecins actifs
    medecins = CustomUser.objects.filter(role='docteur', is_active=True)
    
    return render(request, 'main/nouveau_rdv.html', {
        'medecins': medecins
    })

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

@login_required
def dashboard_medecin(request):
    """Dashboard pour les médecins - VERSION SIMPLE"""
    if request.user.role != 'docteur':
        messages.error(request, 'Accès réservé aux médecins.')
        return redirect('dashboard')
    
    # Récupérer ou créer le profil médecin
    medecin, created = Medecin.objects.get_or_create(user=request.user)
    
    from django.utils import timezone
    today = timezone.now().date()
    current_week = timezone.now().isocalendar()[1]
    current_month = timezone.now().month
    current_year = timezone.now().year
    
    # Calculs simples
    rdv_aujourd_hui = RendezVous.objects.filter(
        medecin=request.user, 
        date_rdv=today
    ).order_by('heure_rdv')
    
    rdv_semaine = RendezVous.objects.filter(
        medecin=request.user,
        date_rdv__week=current_week,
        date_rdv__year=current_year
    ).order_by('date_rdv', 'heure_rdv')
    
    total_patients = RendezVous.objects.filter(
        medecin=request.user
    ).values('patient').distinct().count()
    
    consultations_mois = Consultation.objects.filter(
        rdv__medecin=request.user,
        created_at__month=current_month,
        created_at__year=current_year
    ).count()
    
    context = {
        'medecin': medecin,
        'today': today,
        'rdv_aujourd_hui': rdv_aujourd_hui,
        'rdv_semaine': rdv_semaine,
        'rdv_count': rdv_aujourd_hui.count(),
        'total_patients': total_patients,
        'consultations_mois': consultations_mois,
    }
    
    return render(request, 'dashboard_medecin.html', context)


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

        # Utilisation de TruncDate pour filtrer par jour
        rdv_aujourdhui = RendezVous.objects.annotate(
            date_only=TruncDate('date_rdv')
        ).filter(
            date_only=today
        ).count()

        nouveaux_patients = Patient.objects.annotate(
            created_only=TruncDate('created_at')
        ).filter(
            created_only=today
        ).count()

        context = {
            'user': request.user,
            'secretaire': secretaire,
            'rdv_aujourdhui': rdv_aujourdhui,
            'nouveaux_patients': nouveaux_patients,
        }
        return render(request, 'dashboard_secretaire.html', context)
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement du dashboard: {str(e)}")
        return redirect('home')

# ===== PAGES PATIENTS =====
@login_required
def nouveau_rdv(request):
    # Vérifier les permissions - autoriser médecins, admins et secrétaires
    user_role = getattr(request.user, 'role', None)
    if not (user_role in ['docteur', 'administrateur', 'secretaire'] or request.user.is_superuser):
        messages.error(request, f"Accès refusé. Votre rôle: {user_role}")
        return redirect('dashboard')
    
    # Debug
    print(f"DEBUG - Utilisateur: {request.user.username}, Rôle: {user_role}")
    
    if request.method == 'POST':
        print("=== DONNÉES POST REÇUES ===")
        for key, value in request.POST.items():
            print(f"{key}: {value}")
        print("==========================")
        
        try:
            patient_id = request.POST.get('patient')
            medecin_id = request.POST.get('medecin')
            date_rdv = request.POST.get('date_rdv')
            heure_rdv = request.POST.get('heure_rdv')
            motif = request.POST.get('motif')
            
            # Validation
            if not all([patient_id, medecin_id, date_rdv, heure_rdv, motif]):
                messages.error(request, 'Tous les champs sont obligatoires.')
                return redirect('nouveau_rdv')
            
            # Récupérer les objets
            patient = get_object_or_404(CustomUser, id=patient_id, role='patient')
            medecin = get_object_or_404(CustomUser, id=medecin_id, role='docteur')
            
            # Créer le RDV
            rdv = RendezVous.objects.create(
                patient=patient,
                medecin=medecin,
                date_rdv=date_rdv,
                heure_rdv=heure_rdv,
                motif=motif,
                status='programme'
            )
            
            messages.success(request, f'Rendez-vous créé avec succès pour {patient.get_full_name()}!')
            
            # Redirection selon le rôle
            if user_role == 'docteur':
                return redirect('dashboard_medecin')
            else:
                return redirect('dashboard')
                
        except Exception as e:
            messages.error(request, f'Erreur lors de la création: {str(e)}')
            print(f"Erreur: {e}")
    
    # Récupérer les listes pour le formulaire
    medecins = CustomUser.objects.filter(role='docteur', is_active=True).order_by('first_name', 'last_name')
    patients = CustomUser.objects.filter(role='patient', is_active=True).order_by('first_name', 'last_name')
    
    return render(request, 'nouveau_rdv.html', {
        'medecins': medecins,
        'patients': patients
    })
# @role_required(['patient'])
# def nouveau_rdv(request):
#     if request.method == 'POST':
#         try:
#             medecin_id = request.POST.get('medecin')
#             date_rdv = request.POST.get('date_rdv')
#             heure_rdv = request.POST.get('heure_rdv')
#             motif = request.POST.get('motif')
            
#             if not all([medecin_id, date_rdv, heure_rdv, motif]):
#                 messages.error(request, 'Tous les champs sont obligatoires.')
#                 return redirect('nouveau_rdv')
            
#             medecin = get_object_or_404(CustomUser, id=medecin_id, role='docteur')
            
#             # Combiner date et heure
#             datetime_str = f"{date_rdv} {heure_rdv}"
#             date_rdv_complete = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
#             if is_naive(date_rdv_complete):
#                 date_rdv_complete = make_aware(date_rdv_complete)

#             # Vérifier si la date est dans le futur
#             if date_rdv_complete <= timezone.now():
#                 messages.error(request, 'La date du rendez-vous doit être dans le futur.')
#                 return redirect('nouveau_rdv')
            
#             # Créer le rendez-vous
#             rdv = RendezVous.objects.create(
#                 patient=request.user,
#                 medecin=medecin,
#                 date_rdv=date_rdv_complete,
#                 motif=motif
#             )
            
#             messages.success(request, 'Votre rendez-vous a été programmé avec succès!')
#             return redirect('mes_rdv')
            
#         except Exception as e:
#             messages.error(request, f'Erreur lors de la création du rendez-vous: {str(e)}')
    
#     context = {
#         'medecins': CustomUser.objects.filter(role='docteur', is_active=True),
#         'today': timezone.now().date(),
#     }
#     return render(request, 'nouveau_rdv.html', context)

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

# AJOUTEZ CES VUES À LA FIN DE VOTRE FICHIER views.py :
@login_required
def tous_les_rdv(request):
    rdv_list = RendezVous.objects.all().order_by('-date_rdv')
    return render(request, 'tous_rdv.html', {'rdv_list': rdv_list})
@role_required(['patient'])
def mes_consultations(request):
    """Vue pour voir l'historique des consultations du patient"""
    try:
        # Récupérer toutes les consultations du patient connecté
        consultations_list = Consultation.objects.filter(
            rdv__patient=request.user
        ).order_by('-rdv__date_rdv')
        
        context = {
            'consultations_list': consultations_list,
            'user': request.user
        }
        return render(request, 'consultations.html', context)
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement des consultations: {str(e)}")
        return redirect('dashboard_patient')

@role_required(['patient'])
def mon_dossier_medical(request):
    """Vue pour voir le dossier médical complet du patient"""
    try:
        # Récupérer ou créer le profil patient
        patient, created = Patient.objects.get_or_create(user=request.user)
        
        # Récupérer toutes les données médicales
        rdv_list = RendezVous.objects.filter(patient=request.user).order_by('-date_rdv')
        consultations_list = Consultation.objects.filter(rdv__patient=request.user).order_by('-rdv__date_rdv')
        soins_list = SoinsInfirmier.objects.filter(patient=request.user).order_by('-date_soin')
        
        context = {
            'patient': patient,
            'rdv_list': rdv_list,
            'consultations_list': consultations_list,
            'soins_list': soins_list,
            'user': request.user
        }
        return render(request, 'mon_dossier.html', context)
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement du dossier: {str(e)}")
        return redirect('dashboard_patient')

@role_required(['patient'])
def modifier_profil(request):
    """Vue pour modifier le profil du patient"""
    try:
        # Récupérer ou créer le profil patient
        patient, created = Patient.objects.get_or_create(user=request.user)
        
        if request.method == 'POST':
            form = ProfileUpdateForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profil mis à jour avec succès!')
                return redirect('dashboard_patient')
            else:
                messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
        else:
            form = ProfileUpdateForm(instance=request.user)
        
        context = {
            'form': form,
            'patient': patient,
            'user': request.user
        }
        return render(request, 'modifier_profil.html', context)
    except Exception as e:
        messages.error(request, f"Erreur lors de la modification du profil: {str(e)}")
        return redirect('dashboard_patient')

@role_required(['patient'])
def mes_infos(request):
    """Vue pour voir les informations personnelles du patient"""
    try:
        # Récupérer ou créer le profil patient
        patient, created = Patient.objects.get_or_create(user=request.user)
        
        # Statistiques du patient
        stats = {
            'rdv_total': RendezVous.objects.filter(patient=request.user).count(),
            'rdv_futurs': RendezVous.objects.filter(
                patient=request.user, 
                date_rdv__gte=timezone.now().date()
            ).count(),
            'consultations_total': Consultation.objects.filter(rdv__patient=request.user).count(),
            'soins_total': SoinsInfirmier.objects.filter(patient=request.user).count(),
        }
        
        context = {
            'patient': patient,
            'user': request.user,
            'stats': stats
        }
        return render(request, 'mes_infos.html', context)
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement des informations: {str(e)}")
        return redirect('dashboard_patient')

# Vue pour l'export PDF du dossier médical
@role_required(['patient'])
def download_my_dossier_pdf(request):
    """Télécharger le dossier médical en PDF"""
    try:
        from django.http import HttpResponse
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        import io
        
        # Créer le PDF en mémoire
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Récupérer les données du patient
        patient, created = Patient.objects.get_or_create(user=request.user)
        rdv_list = RendezVous.objects.filter(patient=request.user).order_by('-date_rdv')[:10]
        consultations_list = Consultation.objects.filter(rdv__patient=request.user).order_by('-rdv__date_rdv')[:10]
        
        # En-tête du PDF
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, f"DOSSIER MÉDICAL - {request.user.get_full_name() or request.user.username}")
        
        # Informations patient
        y = height - 100
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "INFORMATIONS PATIENT")
        y -= 20
        
        p.setFont("Helvetica", 10)
        p.drawString(50, y, f"ID Patient: {request.user.user_id}")
        y -= 15
        p.drawString(50, y, f"Nom: {request.user.get_full_name() or request.user.username}")
        y -= 15
        p.drawString(50, y, f"Email: {request.user.email}")
        y -= 15
        p.drawString(50, y, f"Téléphone: {request.user.telephone or 'Non renseigné'}")
        y -= 30
        
        # Rendez-vous récents
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "RENDEZ-VOUS RÉCENTS")
        y -= 20
        
        p.setFont("Helvetica", 9)
        for rdv in rdv_list:
            rdv_text = f"{rdv.date_rdv.strftime('%d/%m/%Y')} - Dr. {rdv.medecin.get_full_name() or rdv.medecin.username} - {rdv.motif[:50]}..."
            p.drawString(50, y, rdv_text)
            y -= 12
            if y < 100:  # Nouvelle page si nécessaire
                p.showPage()
                y = height - 50
        
        # Finaliser le PDF
        p.save()
        buffer.seek(0)
        
        # Retourner la réponse HTTP
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="dossier_medical_{request.user.username}.pdf"'
        return response
        
    except ImportError:
        messages.error(request, 'La génération de PDF n\'est pas disponible. Veuillez installer ReportLab.')
        return redirect('mon_dossier_medical')
    except Exception as e:
        messages.error(request, f"Erreur lors de la génération du PDF: {str(e)}")
        return redirect('mon_dossier_medical')
@login_required
def imprimer_prescription(request, prescription_id):
    if request.user.role != 'docteur':
        raise PermissionDenied()
    
    prescription = get_object_or_404(Prescription, id=prescription_id, medecin=request.user)
    
    # Générer un PDF ou afficher une page d'impression
    return render(request, 'imprimer_prescription.html', {
        'prescription': prescription
    })
@login_required
def nouvelle_consultation(request):
    if request.user.role != 'docteur':
        raise PermissionDenied("Accès réservé aux médecins")
    
    if request.method == 'POST':
        # Logique pour créer une nouvelle consultation
        pass
    
    # Récupérer les patients du médecin
    patients = CustomUser.objects.filter(role='patient')
    
    return render(request, 'nouvelle_consultation.html', {
        'patients': patients
    })
@login_required
def nouvelle_prescription(request):
    if request.user.role != 'docteur':
        messages.error(request, 'Accès réservé aux médecins.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        print("=== DONNÉES POST REÇUES ===")
        for key, value in request.POST.items():
            print(f"{key}: {value}")
        print("==========================")
        
        try:
            patient_id = request.POST.get('patient_id')
            contenu_prescription = request.POST.get('contenu_prescription')
            action = request.POST.get('action')
            
            # Validation
            if not patient_id:
                messages.error(request, 'Veuillez sélectionner un patient.')
                return redirect('nouvelle_prescription')
            
            if not contenu_prescription:
                messages.error(request, 'Veuillez saisir le contenu de la prescription.')
                return redirect('nouvelle_prescription')
            
            # Récupérer le patient
            patient = get_object_or_404(CustomUser, id=patient_id, role='patient')
            
            # Créer la prescription
            prescription = Prescription.objects.create(
                medecin=request.user,
                patient=patient,
                contenu=contenu_prescription
            )
            
            if action == 'sauvegarder':
                messages.success(request, f'Prescription sauvegardée pour {patient.get_full_name()}!')
                return redirect('nouvelle_prescription')
            
            elif action == 'imprimer':
                # Rediriger vers une vue d'impression ou générer un PDF
                messages.success(request, f'Prescription créée pour {patient.get_full_name()}!')
                return redirect('imprimer_prescription', prescription_id=prescription.id)
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la sauvegarde : {str(e)}')
            print(f"Erreur: {e}")
    
    # Récupérer tous les patients
    patients = CustomUser.objects.filter(role='patient', is_active=True).order_by('first_name', 'last_name')
    
    return render(request, 'nouvelle_prescription.html', {
        'patients': patients,
        'medecin': request.user
    })   
# @login_required
# def nouvelle_prescription(request):
#     if request.user.role != 'docteur':
#         messages.error(request, 'Accès réservé aux médecins.')
#         return redirect('dashboard')
    
#     if request.method == 'POST':
#         # Traitement du formulaire
#         pass
    
#     # CORRECTION : Récupérer tous les patients avec leurs noms
#     patients = CustomUser.objects.filter(role='patient', is_active=True).order_by('first_name', 'last_name')
    
#     return render(request, 'nouvelle_prescription.html', {
#         'patients': patients,
#         'medecin': request.user
#     }) /                                                                                                                                 
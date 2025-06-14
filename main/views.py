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
from .models import CustomUser, Patient, RendezVous, SoinsInfirmier, Consultation, Medecin, Infirmier, Secretaire
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
    """Télécharger le dossier médical en PDF avec header ESCO"""
    if request.user.role != 'patient':
        messages.error(request, 'Accès réservé aux patients.')
        return redirect('home')
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="dossier_medical_{request.user.username}_{datetime.date.today().strftime("%Y%m%d")}.pdf"'
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Couleurs ESCO
    purple_color = HexColor('#7c3aed')
    
    # Style pour header ESCO
    header_style = ParagraphStyle(
        'ESCOHeader',
        parent=styles['Heading1'],
        fontSize=28,
        spaceAfter=10,
        textColor=purple_color,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    clinic_style = ParagraphStyle(
        'ClinicInfo',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    # **HEADER ESCO AMÉLIORÉ**
    story.append(Paragraph("🏥 CLINIQUE ESCO", header_style))
    story.append(Paragraph("Système Hospitalier - Soins de Qualité", clinic_style))
    story.append(Paragraph("📍 Adresse de la clinique | ☎️ Téléphone | 🌐 www.esco-clinic.com", clinic_style))
    story.append(Spacer(1, 20))
    
    # Ligne de séparation
    story.append(Paragraph("<hr/>", styles['Normal']))
    story.append(Spacer(1, 10))
    
    # Titre du document
    title_style = ParagraphStyle(
        'DocumentTitle',
        parent=styles['Heading2'],
        fontSize=18,
        spaceAfter=30,
        textColor=purple_color,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    story.append(Paragraph(f"DOSSIER MÉDICAL - {request.user.get_full_name() or request.user.username}", title_style))
    story.append(Paragraph(f"Généré le {datetime.date.today().strftime('%d/%m/%Y')}", clinic_style))
    story.append(Spacer(1, 20))
    
    # Créer la réponse HTTP avec le type de contenu PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="dossier_medical_{request.user.username}_{datetime.date.today().strftime("%Y%m%d")}.pdf"'
    
    # Créer le buffer
    buffer = BytesIO()
    
    # Créer le document PDF
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Couleurs personnalisées
    purple_color = HexColor('#7c3aed')
    light_purple = HexColor('#a855f7')
    
    # Style personnalisé pour le titre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=purple_color,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Style pour les sous-titres
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        textColor=purple_color,
        fontName='Helvetica-Bold'
    )
    
    # Style pour le texte normal
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
        fontName='Helvetica'
    )
    
    # Récupérer les données
    patient, created = Patient.objects.get_or_create(user=request.user)
    rdv_list = RendezVous.objects.filter(patient=request.user).order_by('-date_rdv')
    consultations_list = Consultation.objects.filter(rdv__patient=request.user).order_by('-rdv__date_rdv')
    
    # **HEADER DU DOCUMENT**
    story.append(Paragraph("🏥 ESCO - SYSTÈME HOSPITALIER", title_style))
    story.append(Paragraph(f"Dossier Médical de {request.user.get_full_name() or request.user.username}", subtitle_style))
    story.append(Paragraph(f"Généré le {datetime.date.today().strftime('%d/%m/%Y')}", normal_style))
    story.append(Spacer(1, 20))
    
    # **INFORMATIONS PERSONNELLES**
    story.append(Paragraph("📋 Informations Personnelles", subtitle_style))
    
    personal_data = [
        ['Nom complet:', request.user.get_full_name() or request.user.username],
        ['ID Patient:', request.user.user_id or 'Non défini'],
        ['Email:', request.user.email or 'Non renseigné'],
        ['Téléphone:', request.user.telephone or 'Non renseigné'],
        ['Date de naissance:', request.user.date_naissance.strftime('%d/%m/%Y') if request.user.date_naissance else 'Non renseignée'],
        ['Groupe sanguin:', patient.groupe_sanguin or 'Non défini'],
        ['Adresse:', request.user.adresse or 'Non renseignée'],
    ]
    
    personal_table = Table(personal_data, colWidths=[2*inch, 4*inch])
    personal_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), HexColor('#f8fafc')),
        ('TEXTCOLOR', (0, 0), (0, -1), purple_color),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(personal_table)
    story.append(Spacer(1, 20))
    
    # **STATISTIQUES MÉDICALES**
    story.append(Paragraph("📊 Statistiques Médicales", subtitle_style))
    
    stats_data = [
        ['Total des rendez-vous:', str(rdv_list.count())],
        ['Total des consultations:', str(consultations_list.count())],
        ['Dernière consultation:', consultations_list.first().rdv.date_rdv.strftime('%d/%m/%Y') if consultations_list.exists() else 'Aucune'],
        ['Prochain rendez-vous:', rdv_list.filter(date_rdv__gte=datetime.date.today()).first().date_rdv.strftime('%d/%m/%Y') if rdv_list.filter(date_rdv__gte=datetime.date.today()).exists() else 'Aucun'],
    ]
    
    stats_table = Table(stats_data, colWidths=[2.5*inch, 3.5*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), HexColor('#f0f9ff')),
        ('TEXTCOLOR', (0, 0), (0, -1), purple_color),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(stats_table)
    story.append(Spacer(1, 20))
    
    # **HISTORIQUE DES RENDEZ-VOUS**
    if rdv_list.exists():
        story.append(Paragraph("📅 Historique des Rendez-vous", subtitle_style))
        
        rdv_data = [['Date', 'Heure', 'Médecin', 'Motif', 'Statut']]
        
        for rdv in rdv_list[:10]:  # Limiter à 10 derniers RDV
            rdv_data.append([
                rdv.date_rdv.strftime('%d/%m/%Y'),
                rdv.heure_rdv.strftime('%H:%M'),
                f"Dr. {rdv.medecin.get_full_name() or rdv.medecin.username}",
                rdv.motif[:30] + '...' if len(rdv.motif) > 30 else rdv.motif,
                rdv.get_status_display() if hasattr(rdv, 'get_status_display') else 'Programmé'
            ])
        
        rdv_table = Table(rdv_data, colWidths=[1*inch, 0.8*inch, 1.5*inch, 2*inch, 1*inch])
        rdv_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), purple_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#ffffff'), HexColor('#f8fafc')]),
        ]))
        
        story.append(rdv_table)
        story.append(Spacer(1, 20))
    
    # **HISTORIQUE DES CONSULTATIONS**
    if consultations_list.exists():
        story.append(Paragraph("🩺 Historique des Consultations", subtitle_style))
        
        for consultation in consultations_list[:5]:  # Limiter à 5 dernières consultations
            story.append(Paragraph(f"<b>Date:</b> {consultation.rdv.date_rdv.strftime('%d/%m/%Y')}", normal_style))
            story.append(Paragraph(f"<b>Médecin:</b> Dr. {consultation.rdv.medecin.get_full_name() or consultation.rdv.medecin.username}", normal_style))
            story.append(Paragraph(f"<b>Diagnostic:</b> {consultation.diagnostic or 'Non renseigné'}", normal_style))
            story.append(Paragraph(f"<b>Traitement:</b> {consultation.traitement or 'Non renseigné'}", normal_style))
            story.append(Spacer(1, 10))
    
    # **FOOTER**
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=HexColor('#6b7280'),
        alignment=TA_CENTER
    )
    story.append(Paragraph("Ce document a été généré automatiquement par le système ESCO", footer_style))
    story.append(Paragraph("Pour toute question, contactez votre établissement de santé", footer_style))
    
    # Construire le PDF
    doc.build(story)
    
    # Récupérer la valeur du buffer et la nettoyer
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response


def home(request):
    """Page d'accueil temporaire"""
    return HttpResponse("ESCO - Système de gestion hospitalière")

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
    user = request.user
    medecins = CustomUser.objects.filter(role='docteur', is_active=True)

    if request.method == 'POST':
        form = RendezVousForm(request.POST, medecins=medecins)
        if form.is_valid():
            rdv = form.save(commit=False)
            rdv.patient = user  # ou selon rôle
            rdv.save()
            messages.success(request, "Rendez-vous enregistré avec succès.")
            return redirect('dashboard_patient')
    else:
        form = RendezVousForm(medecins=medecins)

    context = {
        'form': form,
    }
    return render(request, 'nouveau_rdv.html', context)

# def nouveau_rdv(request):
#     # Vérification manuelle des permissions
#     user_role = getattr(request.user, 'role', None)
#     print(f"DEBUG - Role de l'utilisateur: {user_role}")  # Pour déboguer
    
#     if not (user_role == 'docteur' or request.user.is_superuser):
#         messages.error(request, f"Accès refusé. Votre rôle: {user_role}")
#         return redirect('dashboard_medecin')
#     if request.method == 'POST':
#         # Traitement manuel des données du formulaire
#         medecin_id = request.POST.get('medecin')
#         date_rdv = request.POST.get('date_rdv')
#         heure_rdv = request.POST.get('heure_rdv')
#         motif = request.POST.get('motif')
        
#         # Validation
#         errors = []
#         if not medecin_id:
#             errors.append('Veuillez sélectionner un médecin.')
#         if not date_rdv:
#             errors.append('Veuillez sélectionner une date.')
#         if not heure_rdv:
#             errors.append('Veuillez sélectionner une heure.')
#         if not motif:
#             errors.append('Veuillez saisir un motif.')
            
#         if errors:
#             for error in errors:
#                 messages.error(request, error)
#         else:
#             try:
#                 # Créer le rendez-vous
#                 medecin = CustomUser.objects.get(id=medecin_id, role='docteur')
#                 rdv = RendezVous.objects.create(
#                     patient=request.user,
#                     medecin=medecin,
#                     date_rdv=date_rdv,
#                     heure_rdv=heure_rdv,
#                     motif=motif,
#                     status='programme'
#                 )
#                 messages.success(request, 'Votre rendez-vous a été programmé avec succès!')
#                 return redirect('mes_rdv')
#             except Exception as e:
#                 messages.error(request, f'Erreur lors de la création du rendez-vous: {str(e)}')

#     # Récupérer tous les médecins actifs
#     medecins = CustomUser.objects.filter(role='docteur', is_active=True)
    
#     return render(request, 'main/nouveau_rdv.html', {
#         'medecins': medecins
#     })
# Dans views.py
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
    """Vue des consultations pour le médecin"""
    if request.user.role != 'docteur':
        messages.error(request, 'Accès réservé aux médecins.')
        return redirect('home')
    
    rdv_list = RendezVous.objects.filter(medecin=request.user).order_by('-date_rdv')
    
    context = {
        'rdv_list': rdv_list,
        'today': timezone.now().date(),
    }
    return render(request, 'mes_consultations_medecin.html', context)

@login_required
def liste_patients(request):
    """Liste des patients du médecin"""
    if request.user.role != 'docteur':
        messages.error(request, 'Accès réservé aux médecins.')
        return redirect('home')
    
    # Patients ayant eu des RDV avec ce médecin
    patients = CustomUser.objects.filter(
        rdv_patient__medecin=request.user,
        role='patient'
    ).distinct()
    
    context = {
        'patients': patients,
    }
    return render(request, 'liste_patients.html', context)

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
            if is_naive(date_rdv_complete):
                date_rdv_complete = make_aware(date_rdv_complete)

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

# AJOUTEZ CES VUES À LA FIN DE VOTRE FICHIER views.py :

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
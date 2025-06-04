# main/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import CustomUser, Patient, RendezVous, SoinsInfirmier
from .forms import CustomUserCreationForm
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404

@login_required
@staff_member_required
def download_dossier_pdf(request, patient_id):
    """Télécharger le dossier médical d'un patient"""
    try:
        from .models import Patient, RendezVous, Consultation, SoinsInfirmier
        
        patient = get_object_or_404(Patient, id=patient_id)
        rdv_list = RendezVous.objects.filter(patient=patient.user).order_by('-date_rdv')
        consultations = Consultation.objects.filter(rdv__patient=patient.user).order_by('-created_at')
        soins = SoinsInfirmier.objects.filter(patient=patient.user).order_by('-date_soin')
        
        # Version PDF basique
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        import io
        
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # En-tête
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, 750, "🏥 DOSSIER MÉDICAL ESCO")
        
        p.setFont("Helvetica-Bold", 14)
        p.drawString(100, 720, f"Patient: {patient.get_nom_complet()}")
        
        p.setFont("Helvetica", 12)
        y_position = 690
        
        # Informations patient
        p.drawString(100, y_position, f"Numéro Patient: {patient.numero_patient}")
        y_position -= 20
        p.drawString(100, y_position, f"Téléphone: {patient.user.telephone}")
        y_position -= 20
        p.drawString(100, y_position, f"Groupe Sanguin: {patient.groupe_sanguin or 'Non renseigné'}")
        y_position -= 20
        
        if patient.allergies:
            p.setFont("Helvetica-Bold", 12)
            p.drawString(100, y_position, "⚠️ ALLERGIES:")
            y_position -= 15
            p.setFont("Helvetica", 10)
            p.drawString(120, y_position, patient.allergies[:80])
            y_position -= 25
        
        # Historique RDV
        p.setFont("Helvetica-Bold", 12)
        p.drawString(100, y_position, f"Rendez-vous récents: ({rdv_list.count()})")
        y_position -= 20
        
        p.setFont("Helvetica", 10)
        for rdv in rdv_list[:5]:  # Limiter à 5
            rdv_text = f"• {rdv.date_rdv.strftime('%d/%m/%Y')} - Dr. {rdv.medecin.username} - {rdv.motif[:50]}"
            p.drawString(120, y_position, rdv_text)
            y_position -= 15
            if y_position < 100:
                break
        
        # Footer
        p.setFont("Helvetica", 8)
        p.drawString(100, 50, f"Document généré le {timezone.now().strftime('%d/%m/%Y à %H:%M')} - Système ESCO")
        
        p.showPage()
        p.save()
        
        pdf = buffer.getvalue()
        buffer.close()
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="dossier_{patient.user.username}.pdf"'
        response.write(pdf)
        return response
        
    except Exception as e:
        return HttpResponse(f"Erreur lors de la génération: {str(e)}", status=500)

@login_required
@staff_member_required
def download_ordonnance_pdf(request, consultation_id):
    """Télécharger l'ordonnance d'une consultation"""
    try:
        from .models import Consultation
        
        consultation = get_object_or_404(Consultation, id=consultation_id)
        
        # Version PDF basique pour ordonnance
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        import io
        
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # En-tête ordonnance
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, 750, "💊 ORDONNANCE MÉDICALE ESCO")
        
        p.setFont("Helvetica-Bold", 14)
        p.drawString(100, 710, f"Dr. {consultation.rdv.medecin.username}")
        
        p.setFont("Helvetica", 12)
        p.drawString(100, 680, f"Patient: {consultation.rdv.patient.username}")
        p.drawString(100, 660, f"Date: {consultation.rdv.date_rdv.strftime('%d/%m/%Y')}")
        
        # Diagnostic
        p.setFont("Helvetica-Bold", 12)
        p.drawString(100, 620, "DIAGNOSTIC:")
        p.setFont("Helvetica", 10)
        p.drawString(100, 600, consultation.diagnostic[:100])
        
        # Traitement
        p.setFont("Helvetica-Bold", 12)
        p.drawString(100, 560, "TRAITEMENT PRESCRIT:")
        p.setFont("Helvetica", 10)
        
        y_pos = 540
        lines = consultation.traitement.split('\n')
        for line in lines[:10]:  # Limiter à 10 lignes
            p.drawString(100, y_pos, line[:80])
            y_pos -= 15
        
        # Footer
        p.setFont("Helvetica", 8)
        p.drawString(100, 100, "Ordonnance à présenter en pharmacie.")
        p.drawString(100, 50, f"Document généré le {timezone.now().strftime('%d/%m/%Y à %H:%M')} - Système ESCO")
        
        p.showPage()
        p.save()
        
        pdf = buffer.getvalue()
        buffer.close()
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="ordonnance_{consultation.rdv.patient.username}_{consultation.rdv.date_rdv.strftime("%Y%m%d")}.pdf"'
        response.write(pdf)
        return response
        
    except Exception as e:
        return HttpResponse(f"Erreur lors de la génération: {str(e)}", status=500)




@login_required
def download_my_dossier_pdf(request):
    """Permettre aux patients de télécharger leur propre dossier"""
    if request.user.role == 'patient':
        try:
            patient = Patient.objects.get(user=request.user)
            return download_dossier_pdf(request, patient.id)
        except Patient.DoesNotExist:
            return HttpResponse("Dossier patient introuvable", status=404)
    else:
        return HttpResponse("Accès non autorisé", status=403)

# Dans views.py, ajouter cette vue :

@login_required
def dashboard_admin(request):
    if request.user.role != 'administrateur':
        messages.error(request, "Accès non autorisé.")
        return redirect('dashboard')
    
    context = {
        'total_users': CustomUser.objects.count(),
        'total_doctors': CustomUser.objects.filter(role='medecin').count(),
        'total_nurses': CustomUser.objects.filter(role='infirmier').count(),
        'total_patients': Patient.objects.count(),
        'total_appointments_today': RendezVous.objects.filter(date=timezone.now().date()).count(),
        'recent_users': CustomUser.objects.order_by('-date_joined')[:5],
    }
    return render(request, 'dashboard_admin.html', context)


# Page d'accueil
def home(request):
    return render(request, 'home.html')

# Vue de connexion
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
                if user.role == 'patient':
                    return redirect('dashboard_patient')
                elif user.role == 'docteur':
                    return redirect('dashboard_medecin')
                elif user.role == 'infirmier':
                    return redirect('dashboard_infirmier')
                elif user.role == 'secretaire':
                    return redirect('dashboard_secretaire')
                elif user.is_staff:
                    return redirect('dashboard_admin')
                else:
                    return redirect('home')
            else:
                messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {'form': form})

# Vue d'inscription
def inscription(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Compte créé pour {username}! Vous pouvez maintenant vous connecter.')
            return redirect('login')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')

    else:
        form = CustomUserCreationForm()
    
    return render(request, 'inscription.html', {'form': form})

# Vue de déconnexion
def logout_view(request):
    logout(request)
    messages.info(request, 'Vous avez été déconnecté avec succès.')
    return redirect('home')

# Dashboard principal avec redirection
@login_required
def dashboard(request):
    if request.user.is_staff:
        return redirect('dashboard_admin')
    elif request.user.role == 'docteur':
        return redirect('dashboard_medecin')
    elif request.user.role == 'infirmier':
        return redirect('dashboard_infirmier')
    elif request.user.role == 'secretaire':
        return redirect('dashboard_secretaire')
    elif request.user.role == 'patient':
        return redirect('dashboard_patient')
    else:
        return redirect('home')

# Dashboard patient
@login_required
def dashboard_patient(request):
    context = {
        'user': request.user,
        'rdv_a_venir': RendezVous.objects.filter(
            patient=request.user, 
            date_rdv__gte=timezone.now()
        ).count(),
        'message': 'Bienvenue dans votre espace patient',
    }
    return render(request, 'dashboard_patient.html', context)

# Dashboard médecin
@login_required
def dashboard_medecin(request):
    if request.user.role != 'docteur':
        messages.error(request, "Accès non autorisé.")
        return redirect('home')
    
    today = timezone.now().date()
    context = {
        'user': request.user,
        'rdv_aujourd_hui': RendezVous.objects.filter(
            medecin=request.user, 
            date_rdv__date=today
        ).count(),
        'patients_total': RendezVous.objects.filter(medecin=request.user).values('patient').distinct().count(),
        'message': 'Bienvenue dans votre espace médecin',
    }
    return render(request, 'dashboard_medecin.html', context)

# Dashboard infirmier
@login_required
def dashboard_infirmier(request):
    if request.user.role != 'infirmier':
        messages.error(request, "Accès non autorisé.")
        return redirect('home')
    
    today = timezone.now().date()
    context = {
        'user': request.user,
        'soins_aujourd_hui': SoinsInfirmier.objects.filter(
            infirmier=request.user, 
            date_soin__date=today
        ).count(),
        'patients_suivis': SoinsInfirmier.objects.filter(
            infirmier=request.user
        ).values('patient').distinct().count(),
        'soins_en_attente': SoinsInfirmier.objects.filter(
            infirmier=request.user, 
            date_soin__gte=timezone.now()
        ).count(),
        'soins_termines': SoinsInfirmier.objects.filter(
            infirmier=request.user, 
            date_soin__lt=timezone.now()
        ).count(),
    }
    return render(request, 'dashboard_infirmier.html', context)

# Dashboard secrétaire
@login_required
def dashboard_secretaire(request):
    if request.user.role != 'secretaire':
        messages.error(request, "Accès non autorisé.")
        return redirect('home')
    
    today = timezone.now().date()
    context = {
        'user': request.user,
        'rdv_aujourd_hui': RendezVous.objects.filter(date_rdv__date=today).count(),
        'total_patients': CustomUser.objects.filter(role='patient').count(),
        'total_doctors': CustomUser.objects.filter(role='docteur').count(),
        'appels_en_attente': 0,  # À implémenter
        'validations_attente': CustomUser.objects.filter(is_active=False).count(),
        'factures_jour': 0,  # À implémenter
    }
    return render(request, 'dashboard_secretaire.html', context)

# Dashboard admin
@login_required
def dashboard_admin(request):
    if not request.user.is_staff:
        messages.error(request, "Accès non autorisé.")
        return redirect('home')
    
    recent_users = CustomUser.objects.order_by('-date_joined')[:5]
    
    context = {
        'total_users': CustomUser.objects.count(),
        'total_patients': CustomUser.objects.filter(role='patient').count(),
        'total_doctors': CustomUser.objects.filter(role='docteur').count(),
        'total_secretaires': CustomUser.objects.filter(role='secretaire').count(),
        'recent_users': recent_users,
    }
    return render(request, 'dashboard_admin.html', context)
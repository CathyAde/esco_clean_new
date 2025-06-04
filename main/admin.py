from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import CustomUser, Patient, RendezVous, Consultation, SoinsInfirmier, Planning

# ===== ADMIN CUSTOMUSER =====
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'telephone', 'is_active', 'date_joined', 'colored_status')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'telephone')
    ordering = ('-date_joined',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informations ESCO', {
            'fields': ('role', 'telephone', 'adresse', 'date_naissance', 'specialite', 'numero_licence'),
            'classes': ('wide',)
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations ESCO', {
            'fields': ('role', 'telephone', 'adresse', 'date_naissance', 'specialite', 'numero_licence'),
            'classes': ('wide',)
        }),
    )
    
    def colored_status(self, obj):
        if obj.is_active:
            color = 'green'
            status = 'Actif'
            icon = 'fas fa-check-circle'
        else:
            color = 'red'
            status = 'Inactif'
            icon = 'fas fa-times-circle'
        return format_html(
            '<span style="color: {}; font-weight: bold;"><i class="{}"></i> {}</span>',
            color, icon, status
        )
    colored_status.short_description = 'Statut'

# ===== ADMIN PATIENT =====
@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('get_nom_complet', 'numero_patient', 'get_telephone', 'groupe_sanguin', 'get_allergies', 'actions_rapides')
    list_filter = ('groupe_sanguin', 'user__date_joined')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'numero_patient', 'user__telephone')
    ordering = ('-user__date_joined',)
    
    fieldsets = (
        ('Utilisateur Associé', {
            'fields': ('user',),
            'classes': ('wide',)
        }),
        ('Informations Patient', {
            'fields': ('numero_patient', 'groupe_sanguin'),
            'classes': ('wide',)
        }),
        ('Informations Médicales', {
            'fields': ('allergies', 'antecedents'),
            'classes': ('wide',)
        }),
    )
    
    def get_nom_complet(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}" if obj.user.first_name or obj.user.last_name else obj.user.username
    get_nom_complet.short_description = 'Nom Complet'
    
    def get_telephone(self, obj):
        return obj.user.telephone or 'Non renseigné'
    get_telephone.short_description = 'Téléphone'
    
    def get_allergies(self, obj):
        if obj.allergies:
            return obj.allergies[:50] + "..." if len(obj.allergies) > 50 else obj.allergies
        return "Aucune"
    get_allergies.short_description = 'Allergies'
    
    def actions_rapides(self, obj):
        actions = []
        try:
            # Lien pour nouveau RDV
            url_rdv = reverse('admin:main_rendezvous_add') + f'?patient={obj.user.id}'
            actions.append(f'<a class="button" href="{url_rdv}">📅 Nouveau RDV</a>')
            
            # Lien PDF dossier
            url_pdf = reverse('download_dossier_pdf', args=[obj.id])
            actions.append(f'<a class="button" href="{url_pdf}" target="_blank">📄 Dossier PDF</a>')
        except:
            pass
        return format_html(' '.join(actions)) if actions else 'N/A'
    actions_rapides.short_description = 'Actions'

# ===== ADMIN RENDEZ-VOUS =====
@admin.register(RendezVous)
class RendezVousAdmin(admin.ModelAdmin):
    list_display = ('get_patient', 'get_medecin', 'date_rdv', 'motif', 'status_display', 'actions_rdv')
    list_filter = ('status', 'date_rdv', 'medecin__role')
    search_fields = ('patient__username', 'patient__first_name', 'patient__last_name', 'medecin__username', 'motif')
    ordering = ('-date_rdv',)
    date_hierarchy = 'date_rdv'
    
    fieldsets = (
        ('Participants', {
            'fields': ('patient', 'medecin'),
            'classes': ('wide',)
        }),
        ('Rendez-vous', {
            'fields': ('date_rdv', 'motif', 'status'),
            'classes': ('wide',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('wide',)
        }),
    )
    
    def get_patient(self, obj):
        name = f"{obj.patient.first_name} {obj.patient.last_name}" if obj.patient.first_name or obj.patient.last_name else obj.patient.username
        return name
    get_patient.short_description = 'Patient'
    
    def get_medecin(self, obj):
        return f"Dr. {obj.medecin.first_name} {obj.medecin.last_name}" if obj.medecin.first_name or obj.medecin.last_name else obj.medecin.username
    get_medecin.short_description = 'Médecin'
    
    def status_display(self, obj):
        colors = {
            'programme': '#3b82f6',
            'confirme': '#10b981',
            'en_cours': '#f59e0b',
            'termine': '#6b7280',
            'annule': '#ef4444'
        }
        icons = {
            'programme': 'fas fa-calendar',
            'confirme': 'fas fa-check',
            'en_cours': 'fas fa-play',
            'termine': 'fas fa-check-double',
            'annule': 'fas fa-times'
        }
        color = colors.get(obj.status, '#6b7280')
        icon = icons.get(obj.status, 'fas fa-question')
        return format_html(
            '<span style="color: {}; font-weight: bold;"><i class="{}"></i> {}</span>',
            color, icon, obj.get_status_display()
        )
    status_display.short_description = 'Statut'
    
    def actions_rdv(self, obj):
        actions = []
        if obj.status in ['confirme', 'en_cours'] and not hasattr(obj, 'consultation'):
            url_consultation = reverse('admin:main_consultation_add') + f'?rdv={obj.id}'
            actions.append(f'<a class="button" href="{url_consultation}">🩺 Créer Consultation</a>')
        elif hasattr(obj, 'consultation'):
            actions.append('<span style="color: green;">✅ Consultation faite</span>')
        return format_html(' '.join(actions)) if actions else 'N/A'
    actions_rdv.short_description = 'Actions'

# ===== ADMIN CONSULTATION =====
@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('get_patient', 'get_medecin', 'get_date', 'get_diagnostic_court', 'actions_consultation')
    list_filter = ('rdv__date_rdv', 'rdv__medecin')
    search_fields = ('rdv__patient__username', 'rdv__patient__first_name', 'rdv__patient__last_name', 'diagnostic', 'symptomes')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Rendez-vous Associé', {
            'fields': ('rdv',),
            'classes': ('wide',)
        }),
        ('Examen', {
            'fields': ('symptomes', 'diagnostic'),
            'classes': ('wide',)
        }),
        ('Traitement', {
            'fields': ('traitement', 'observations'),
            'classes': ('wide',)
        }),
    )
    
    def get_patient(self, obj):
        patient = obj.rdv.patient
        return f"{patient.first_name} {patient.last_name}" if patient.first_name or patient.last_name else patient.username
    get_patient.short_description = 'Patient'
    
    def get_medecin(self, obj):
        medecin = obj.rdv.medecin
        return f"Dr. {medecin.first_name} {medecin.last_name}" if medecin.first_name or medecin.last_name else medecin.username
    get_medecin.short_description = 'Médecin'
    
    def get_date(self, obj):
        return obj.rdv.date_rdv.strftime('%d/%m/%Y %H:%M')
    get_date.short_description = 'Date Consultation'
    
    def get_diagnostic_court(self, obj):
        if obj.diagnostic:
            return obj.diagnostic[:60] + "..." if len(obj.diagnostic) > 60 else obj.diagnostic
        return "Non renseigné"
    get_diagnostic_court.short_description = 'Diagnostic'
    
    def actions_consultation(self, obj):
        actions = []
        if obj.traitement:
            try:
                url_ordonnance = reverse('download_ordonnance_pdf', args=[obj.id])
                actions.append(f'<a class="button" href="{url_ordonnance}" target="_blank">💊 Ordonnance PDF</a>')
            except:
                pass
        else:
            actions.append('<span style="color: orange;">⚠️ Pas de traitement</span>')
        return format_html(' '.join(actions)) if actions else 'N/A'
    actions_consultation.short_description = 'Documents'

# ===== ADMIN SOINS INFIRMIER =====
@admin.register(SoinsInfirmier)
class SoinsInfirmierAdmin(admin.ModelAdmin):
    list_display = ('get_patient', 'get_infirmier', 'type_soin', 'date_soin', 'get_description_courte')
    list_filter = ('type_soin', 'date_soin', 'infirmier')
    search_fields = ('patient__username', 'patient__first_name', 'patient__last_name', 'infirmier__username', 'description')
    ordering = ('-date_soin',)
    date_hierarchy = 'date_soin'
    
    fieldsets = (
        ('Participants', {
            'fields': ('patient', 'infirmier'),
            'classes': ('wide',)
        }),
        ('Soin', {
            'fields': ('type_soin', 'description', 'date_soin'),
            'classes': ('wide',)
        }),
        ('Observations', {
            'fields': ('observations',),
            'classes': ('wide',)
        }),
    )
    
    def get_patient(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}" if obj.patient.first_name or obj.patient.last_name else obj.patient.username
    get_patient.short_description = 'Patient'
    
    def get_infirmier(self, obj):
        return f"{obj.infirmier.first_name} {obj.infirmier.last_name}" if obj.infirmier.first_name or obj.infirmier.last_name else obj.infirmier.username
    get_infirmier.short_description = 'Infirmier'
    
    def get_description_courte(self, obj):
        return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
    get_description_courte.short_description = 'Description'

# ===== ADMIN PLANNING =====
@admin.register(Planning)
class PlanningAdmin(admin.ModelAdmin):
    list_display = ('get_user', 'date', 'heure_debut', 'heure_fin', 'disponible_display', 'get_notes_courtes')
    list_filter = ('disponible', 'date', 'user__role')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'notes')
    ordering = ('-date', 'heure_debut')
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user',),
            'classes': ('wide',)
        }),
        ('Horaires', {
            'fields': ('date', 'heure_debut', 'heure_fin', 'disponible'),
            'classes': ('wide',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('wide',)
        }),
    )
    
    def get_user(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}" if obj.user.first_name or obj.user.last_name else obj.user.username
    get_user.short_description = 'Utilisateur'
    
    def disponible_display(self, obj):
        if obj.disponible:
            return format_html('<span style="color: green; font-weight: bold;"><i class="fas fa-check"></i> Disponible</span>')
        else:
            return format_html('<span style="color: red; font-weight: bold;"><i class="fas fa-times"></i> Occupé</span>')
    disponible_display.short_description = 'Disponibilité'
    
    def get_notes_courtes(self, obj):
        if obj.notes:
            return obj.notes[:40] + "..." if len(obj.notes) > 40 else obj.notes
        return "Aucune note"
    get_notes_courtes.short_description = 'Notes'

# ===== PERSONNALISATION DU SITE ADMIN =====
admin.site.site_header = "🏥 Administration ESCO"
admin.site.site_title = "ESCO Admin"
admin.site.index_title = "Panneau d'Administration ESCO - Système de Gestion Hospitalière"
# main/admin.py
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html
from .models import CustomUser, Patient, Medecin, Infirmier, Secretaire, RendezVous, Consultation, SoinsInfirmier, Planning

class ESCOAdminSite(AdminSite):
    site_header = '🏥 ESCO - Administration Médicale'
    site_title = 'ESCO Admin'
    index_title = 'Panneau d\'administration ESCO'
    
    def each_context(self, request):
        context = super().each_context(request)
        context['site_url'] = '/'
        return context

# Créer une instance personnalisée
admin_site = ESCOAdminSite(name='esco_admin')

@admin.register(CustomUser, site=admin_site)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('user_id_display', 'username', 'get_full_name', 'email', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'user_id')
    readonly_fields = ('user_id', 'date_joined', 'last_login')
    
    def user_id_display(self, obj):
        return format_html(
            '<span style="background: linear-gradient(135deg, #7c3aed, #a855f7); color: white; '
            'padding: 0.25rem 0.75rem; border-radius: 20px; font-weight: 600; font-size: 0.8rem;">{}</span>',
            obj.user_id or 'Non défini'
        )
    user_id_display.short_description = 'ID Utilisateur'
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username
    get_full_name.short_description = 'Nom complet'
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('username', 'password', 'user_id')
        }),
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'email', 'telephone', 'adresse', 'date_naissance')
        }),
        ('Rôle et permissions', {
            'fields': ('role', 'specialite', 'numero_licence', 'is_active', 'is_staff', 'is_superuser')
        }),
        ('Dates importantes', {
            'fields': ('date_joined', 'last_login'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Patient, site=admin_site)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('numero_patient_display', 'get_nom_complet', 'groupe_sanguin', 'created_at')
    list_filter = ('groupe_sanguin', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'numero_patient')
    readonly_fields = ('numero_patient', 'created_at')
    
    def numero_patient_display(self, obj):
        return format_html(
            '<span style="background: #10b981; color: white; '
            'padding: 0.25rem 0.75rem; border-radius: 20px; font-weight: 600; font-size: 0.8rem;">{}</span>',
            obj.numero_patient or 'Non défini'
        )
    numero_patient_display.short_description = 'N° Patient'
    
    def get_nom_complet(self, obj):
        """Méthode pour afficher le nom complet du patient"""
        if obj.user.first_name or obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return obj.user.username
    get_nom_complet.short_description = 'Nom complet'

@admin.register(Medecin, site=admin_site)
class MedecinAdmin(admin.ModelAdmin):
    list_display = ('numero_ordre_display', 'get_nom_complet', 'specialite')
    list_filter = ('specialite',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'numero_ordre', 'specialite')
    readonly_fields = ('numero_ordre',)
    
    def numero_ordre_display(self, obj):
        return format_html(
            '<span style="background: #3b82f6; color: white; '
            'padding: 0.25rem 0.75rem; border-radius: 20px; font-weight: 600; font-size: 0.8rem;">{}</span>',
            obj.numero_ordre or 'Non défini'
        )
    numero_ordre_display.short_description = 'N° Ordre'
    
    def get_nom_complet(self, obj):
        return f"Dr. {obj.user.get_full_name() or obj.user.username}"
    get_nom_complet.short_description = 'Nom complet'

@admin.register(Infirmier, site=admin_site)
class InfirmierAdmin(admin.ModelAdmin):
    list_display = ('numero_ordre_display', 'get_nom_complet', 'service')
    list_filter = ('service',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'numero_ordre', 'service')
    readonly_fields = ('numero_ordre',)
    
    def numero_ordre_display(self, obj):
        return format_html(
            '<span style="background: #8b5cf6; color: white; '
            'padding: 0.25rem 0.75rem; border-radius: 20px; font-weight: 600; font-size: 0.8rem;">{}</span>',
            obj.numero_ordre or 'Non défini'
        )
    numero_ordre_display.short_description = 'N° Ordre'
    
    def get_nom_complet(self, obj):
        return f"Inf. {obj.user.get_full_name() or obj.user.username}"
    get_nom_complet.short_description = 'Nom complet'

@admin.register(Secretaire, site=admin_site)
class SecretaireAdmin(admin.ModelAdmin):
    list_display = ('get_nom_complet', 'service')
    list_filter = ('service',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'service')
    
    def get_nom_complet(self, obj):
        return f"Sec. {obj.user.get_full_name() or obj.user.username}"
    get_nom_complet.short_description = 'Nom complet'

@admin.register(RendezVous, site=admin_site)
class RendezVousAdmin(admin.ModelAdmin):
    list_display = ('patient_display', 'medecin_display', 'date_rdv', 'status_display', 'created_at')
    list_filter = ('status', 'date_rdv', 'created_at')
    search_fields = ('patient__username', 'medecin__username', 'motif')
    date_hierarchy = 'date_rdv'
    
    def patient_display(self, obj):
        return format_html(
            '<span style="background: #10b981; color: white; '
            'padding: 0.25rem 0.5rem; border-radius: 15px; font-size: 0.8rem;">{}</span>',
            obj.patient.get_full_name() or obj.patient.username
        )
    patient_display.short_description = 'Patient'
    
    def medecin_display(self, obj):
        return format_html(
            '<span style="background: #3b82f6; color: white; '
            'padding: 0.25rem 0.5rem; border-radius: 15px; font-size: 0.8rem;">Dr. {}</span>',
            obj.medecin.get_full_name() or obj.medecin.username
        )
    medecin_display.short_description = 'Médecin'
    
    def status_display(self, obj):
        colors = {
            'programme': '#f59e0b',
            'confirme': '#3b82f6',
            'en_cours': '#8b5cf6',
            'termine': '#10b981',
            'annule': '#ef4444'
        }
        return format_html(
            '<span style="background: {}; color: white; '
            'padding: 0.25rem 0.75rem; border-radius: 20px; font-weight: 600; font-size: 0.8rem;">{}</span>',
            colors.get(obj.status, '#6b7280'),
            obj.get_status_display()
        )
    status_display.short_description = 'Statut'

@admin.register(Consultation, site=admin_site)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('patient_display', 'medecin_display', 'date_consultation', 'diagnostic_court')
    list_filter = ('created_at',)
    search_fields = ('rdv__patient__username', 'rdv__medecin__username', 'diagnostic', 'symptomes')
    readonly_fields = ('created_at', 'updated_at')
    
    def patient_display(self, obj):
        return obj.rdv.patient.get_full_name() or obj.rdv.patient.username
    patient_display.short_description = 'Patient'
    
    def medecin_display(self, obj):
        return f"Dr. {obj.rdv.medecin.get_full_name() or obj.rdv.medecin.username}"
    medecin_display.short_description = 'Médecin'
    
    def date_consultation(self, obj):
        return obj.rdv.date_rdv
    date_consultation.short_description = 'Date'
    
    def diagnostic_court(self, obj):
        return obj.diagnostic[:50] + '...' if obj.diagnostic and len(obj.diagnostic) > 50 else obj.diagnostic or 'Non renseigné'
    diagnostic_court.short_description = 'Diagnostic'

@admin.register(SoinsInfirmier, site=admin_site)
class SoinsInfirmierAdmin(admin.ModelAdmin):
    list_display = ('patient_display', 'infirmier_display', 'type_soin_display', 'date_soin')
    list_filter = ('type_soin', 'date_soin')
    search_fields = ('patient__username', 'infirmier__username', 'description', 'type_soin')
    date_hierarchy = 'date_soin'
    
    def patient_display(self, obj):
        return obj.patient.get_full_name() or obj.patient.username
    patient_display.short_description = 'Patient'
    
    def infirmier_display(self, obj):
        return f"Inf. {obj.infirmier.get_full_name() or obj.infirmier.username}"
    infirmier_display.short_description = 'Infirmier'
    
    def type_soin_display(self, obj):
        return format_html(
            '<span style="background: #8b5cf6; color: white; '
            'padding: 0.25rem 0.75rem; border-radius: 20px; font-weight: 600; font-size: 0.8rem;">{}</span>',
            obj.get_type_soin_display()
        )
    type_soin_display.short_description = 'Type de soin'

@admin.register(Planning, site=admin_site)
class PlanningAdmin(admin.ModelAdmin):
    list_display = ('user_display', 'jour_display', 'heure_debut', 'heure_fin', 'disponible_display')
    list_filter = ('jour', 'disponible', 'user__role')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    
    def user_display(self, obj):
        return obj.user.get_full_name() or obj.user.username
    user_display.short_description = 'Utilisateur'
    
    def jour_display(self, obj):
        return format_html(
            '<span style="background: #3b82f6; color: white; '
            'padding: 0.25rem 0.75rem; border-radius: 20px; font-weight: 600; font-size: 0.8rem;">{}</span>',
            obj.get_jour_display()
        )
    jour_display.short_description = 'Jour'
    
    def disponible_display(self, obj):
        color = '#10b981' if obj.disponible else '#ef4444'
        text = 'Disponible' if obj.disponible else 'Indisponible'
        return format_html(
            '<span style="background: {}; color: white; '
            'padding: 0.25rem 0.75rem; border-radius: 20px; font-weight: 600; font-size: 0.8rem;">{}</span>',
            color, text
        )
    disponible_display.short_description = 'Statut'

# Enregistrer tous les modèles sur l'admin par défaut aussi (pour compatibilité)
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Patient, PatientAdmin)
admin.site.register(Medecin, MedecinAdmin)
admin.site.register(Infirmier, InfirmierAdmin)
admin.site.register(Secretaire, SecretaireAdmin)
admin.site.register(RendezVous, RendezVousAdmin)
admin.site.register(Consultation, ConsultationAdmin)
admin.site.register(SoinsInfirmier, SoinsInfirmierAdmin)
admin.site.register(Planning, PlanningAdmin) 

# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin
# from django.utils.html import format_html
# from django.urls import reverse, path
# from django.utils.safestring import mark_safe
# from django.contrib.admin import AdminSite
# from django.template.response import TemplateResponse
# from django.shortcuts import render
# from django.db.models import Count
# from .models import CustomUser, Patient, RendezVous, Consultation, SoinsInfirmier, Planning, Medecin, Infirmier, Secretaire

# # ===== SITE ADMIN PERSONNALISÉ ESCO =====
# class ESCOAdminSite(AdminSite):
#     site_header = '🏥 ESCO - Administration Médicale'
#     site_title = 'ESCO Admin'
#     index_title = 'Tableau de bord administrateur - Système de Gestion Hospitalière'
    
#     def get_urls(self):
#         urls = super().get_urls()
#         custom_urls = [
#             path('dashboard/', self.admin_view(self.dashboard_view), name='admin_dashboard'),
#         ]
#         return custom_urls + urls
    
#     def dashboard_view(self, request):
#         """Vue personnalisée du dashboard admin"""
#         from django.utils import timezone
#         today = timezone.now().date()
        
#         # Statistiques générales
#         stats = {
#             'total_patients': Patient.objects.count(),
#             'total_users': CustomUser.objects.count(),
#             'total_medecins': CustomUser.objects.filter(role='docteur').count(),
#             'total_infirmiers': CustomUser.objects.filter(role='infirmier').count(),
#             'total_secretaires': CustomUser.objects.filter(role='secretaire').count(),
#             'rdv_aujourdhui': RendezVous.objects.filter(date_rdv__date=today).count(),
#             'rdv_total': RendezVous.objects.count(),
#             'consultations_total': Consultation.objects.count(),
#             'soins_total': SoinsInfirmier.objects.count(),
#         }
        
#         # Statistiques par rôle
#         users_by_role = CustomUser.objects.values('role').annotate(count=Count('id'))
        
#         # Activités récentes
#         recent_rdv = RendezVous.objects.select_related('patient', 'medecin').order_by('-created_at')[:10]
#         recent_users = CustomUser.objects.order_by('-date_joined')[:10]
#         recent_consultations = Consultation.objects.select_related('rdv__patient', 'rdv__medecin').order_by('-created_at')[:5]
        
#         context = {
#             'title': 'Dashboard ESCO',
#             'stats': stats,
#             'users_by_role': users_by_role,
#             'recent_rdv': recent_rdv,
#             'recent_users': recent_users,
#             'recent_consultations': recent_consultations,
#             'today': today,
#         }
        
#         return TemplateResponse(request, 'admin/esco_dashboard.html', context)
    
#     def index(self, request, extra_context=None):
#         """Page d'accueil personnalisée de l'admin avec statistiques ESCO"""
#         return self.dashboard_view(request)

# # Créer l'instance du site admin personnalisé
# admin_site = ESCOAdminSite(name='esco_admin')

# # ===== ADMIN CUSTOMUSER =====
# @admin.register(CustomUser, site=admin_site)
# class CustomUserAdmin(UserAdmin):
#     list_display = ('user_id', 'username', 'get_full_name', 'email', 'role_colored', 'telephone', 'is_active_colored', 'date_joined', 'actions_user')
#     list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
#     search_fields = ('user_id', 'username', 'email', 'first_name', 'last_name', 'telephone')
#     ordering = ('-date_joined',)
    
#     fieldsets = UserAdmin.fieldsets + (
#         ('🏥 Informations ESCO', {
#             'fields': ('user_id', 'role', 'telephone', 'adresse', 'date_naissance', 'specialite', 'numero_licence'),
#             'classes': ('wide',)
#         }),
#     )
    
#     readonly_fields = ('user_id',)
    
#     add_fieldsets = UserAdmin.add_fieldsets + (
#         ('🏥 Informations ESCO', {
#             'fields': ('role', 'telephone', 'adresse', 'date_naissance', 'specialite', 'numero_licence'),
#             'classes': ('wide',)
#         }),
#     )
    
#     def role_colored(self, obj):
#         colors = {
#             'patient': '#007bff',
#             'docteur': '#28a745',
#             'infirmier': '#e91e63',
#             'secretaire': '#17a2b8',
#             'administrateur': '#6c5ce7'
#         }
#         icons = {
#             'patient': 'fas fa-user-injured',
#             'docteur': 'fas fa-user-md',
#             'infirmier': 'fas fa-user-nurse',
#             'secretaire': 'fas fa-user-tie',
#             'administrateur': 'fas fa-user-shield'
#         }
#         color = colors.get(obj.role, '#6c757d')
#         icon = icons.get(obj.role, 'fas fa-user')
#         return format_html(
#             '<span style="color: {}; font-weight: bold;"><i class="{}"></i> {}</span>',
#             color, icon, obj.get_role_display()
#         )
#     role_colored.short_description = 'Rôle'
    
#     def is_active_colored(self, obj):
#         if obj.is_active:
#             return format_html('<span style="color: green; font-weight: bold;"><i class="fas fa-check-circle"></i> Actif</span>')
#         else:
#             return format_html('<span style="color: red; font-weight: bold;"><i class="fas fa-times-circle"></i> Inactif</span>')
#     is_active_colored.short_description = 'Statut'
    
#     def actions_user(self, obj):
#         actions = []
#         if obj.role == 'patient':
#             try:
#                 patient = Patient.objects.get(user=obj)
#                 url_rdv = reverse('admin:main_rendezvous_add') + f'?patient={obj.id}'
#                 actions.append(f'<a class="button" href="{url_rdv}">📅 Nouveau RDV</a>')
#             except Patient.DoesNotExist:
#                 pass
        
#         return format_html(' '.join(actions))
#     actions_user.short_description = 'Actions'

# # ===== ADMIN PATIENT =====
# @admin.register(Patient, site=admin_site)
# class PatientAdmin(admin.ModelAdmin):
#     list_display = ('numero_patient', 'get_nom_complet', 'get_email', 'get_telephone', 'groupe_sanguin', 'created_at', 'actions_patient')
#     list_filter = ('groupe_sanguin', 'created_at')
#     search_fields = ('numero_patient', 'user__username', 'user__first_name', 'user__last_name', 'user__email')
#     readonly_fields = ('numero_patient', 'created_at')
    
#     fieldsets = (
#         ('👤 Informations Patient', {
#             'fields': ('user', 'numero_patient')
#         }),
#         ('🩸 Informations Médicales', {
#             'fields': ('groupe_sanguin', 'allergies', 'antecedents'),
#             'classes': ('wide',)
#         }),
#         ('📅 Informations Système', {
#             'fields': ('created_at',),
#             'classes': ('collapse',)
#         }),
#     )
    
#     def get_nom_complet(self, obj):
#         return obj.get_nom_complet()
#     get_nom_complet.short_description = 'Nom complet'
    
#     def get_email(self, obj):
#         return obj.user.email
#     get_email.short_description = 'Email'
    
#     def get_telephone(self, obj):
#         return obj.user.telephone or 'Non renseigné'
#     get_telephone.short_description = 'Téléphone'
    
#     def actions_patient(self, obj):
#         actions = []
#         url_rdv = reverse('admin:main_rendezvous_add') + f'?patient={obj.user.id}'
#         actions.append(f'<a class="button" href="{url_rdv}">📅 Nouveau RDV</a>')
        
#         url_dossier = reverse('download_dossier_pdf', args=[obj.id])
#         actions.append(f'<a class="button" href="{url_dossier}">📄 Dossier PDF</a>')
        
#         return format_html(' '.join(actions))
#     actions_patient.short_description = 'Actions'

# # ===== ADMIN RENDEZ-VOUS =====
# @admin.register(RendezVous, site=admin_site)
# class RendezVousAdmin(admin.ModelAdmin):
#     list_display = ('get_rdv_info', 'patient_info', 'medecin_info', 'date_rdv', 'status_colored', 'created_at', 'actions_rdv')
#     list_filter = ('status', 'date_rdv', 'created_at')
#     search_fields = ('patient__username', 'medecin__username', 'motif')
#     date_hierarchy = 'date_rdv'
    
#     fieldsets = (
#         ('👥 Participants', {
#             'fields': ('patient', 'medecin')
#         }),
#         ('📅 Planification', {
#             'fields': ('date_rdv', 'motif', 'status'),
#             'classes': ('wide',)
#         }),
#         ('📝 Notes', {
#             'fields': ('notes',),
#             'classes': ('collapse',)
#         }),
#     )
    
#     def get_rdv_info(self, obj):
#         return f"RDV #{obj.id}"
#     get_rdv_info.short_description = 'RDV'
    
#     def patient_info(self, obj):
#         return format_html(
#             '<strong>{}</strong><br><small>{}</small>',
#             obj.patient.get_full_name() or obj.patient.username,
#             obj.patient.email
#         )
#     patient_info.short_description = 'Patient'
    
#     def medecin_info(self, obj):
#         return format_html(
#             '<strong>Dr. {}</strong><br><small>{}</small>',
#             obj.medecin.get_full_name() or obj.medecin.username,
#             obj.medecin.specialite or 'Généraliste'
#         )
#     medecin_info.short_description = 'Médecin'
    
#     def status_colored(self, obj):
#         colors = {
#             'programme': '#ffc107',
#             'confirme': '#28a745',
#             'en_cours': '#007bff',
#             'termine': '#6c757d',
#             'annule': '#dc3545'
#         }
#         color = colors.get(obj.status, '#6c757d')
#         return format_html(
#             '<span style="background-color: {}; color: white; padding: 0.3rem 0.6rem; border-radius: 4px; font-size: 0.8rem;">{}</span>',
#             color, obj.get_status_display()
#         )
#     status_colored.short_description = 'Statut'
    
#     def actions_rdv(self, obj):
#         actions = []
#         if obj.status == 'confirme':
#             url_consultation = reverse('admin:main_consultation_add') + f'?rdv={obj.id}'
#             actions.append(f'<a class="button" href="{url_consultation}">🩺 Consultation</a>')
        
#         return format_html(' '.join(actions))
#     actions_rdv.short_description = 'Actions'

# # ===== ADMIN CONSULTATION =====
# @admin.register(Consultation, site=admin_site)
# class ConsultationAdmin(admin.ModelAdmin):
#     list_display = ('get_consultation_info', 'get_patient', 'get_medecin', 'get_date', 'has_traitement', 'created_at')
#     list_filter = ('created_at', 'rdv__date_rdv')
#     search_fields = ('rdv__patient__username', 'rdv__medecin__username', 'diagnostic', 'symptomes')
    
#     fieldsets = (
#         ('🔗 Rendez-vous', {
#             'fields': ('rdv',)
#         }),
#         ('🩺 Examen', {
#             'fields': ('symptomes', 'diagnostic'),
#             'classes': ('wide',)
#         }),
#         ('💊 Traitement', {
#             'fields': ('traitement',),
#             'classes': ('wide',)
#         }),
#         ('📝 Observations', {
#             'fields': ('observations',),
#             'classes': ('collapse',)
#         }),
#     )
    
#     def get_consultation_info(self, obj):
#         return f"Consultation #{obj.id}"
#     get_consultation_info.short_description = 'Consultation'
    
#     def get_patient(self, obj):
#         return obj.rdv.patient.get_full_name() or obj.rdv.patient.username
#     get_patient.short_description = 'Patient'
    
#     def get_medecin(self, obj):
#         return f"Dr. {obj.rdv.medecin.get_full_name() or obj.rdv.medecin.username}"
#     get_medecin.short_description = 'Médecin'
    
#     def get_date(self, obj):
#         return obj.rdv.date_rdv.strftime('%d/%m/%Y %H:%M')
#     get_date.short_description = 'Date RDV'
    
#     def has_traitement(self, obj):
#         if obj.traitement:
#             return format_html('<span style="color: green;">✓ Oui</span>')
#         return format_html('<span style="color: red;">✗ Non</span>')
#     has_traitement.short_description = 'Traitement'

# # Enregistrer les autres modèles
# admin_site.register(Medecin)
# admin_site.register(Infirmier)
# admin_site.register(Secretaire)
# admin_site.register(SoinsInfirmier)
# admin_site.register(Planning)





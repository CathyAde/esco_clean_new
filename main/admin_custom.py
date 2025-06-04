# main/admin_custom.py
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.urls import reverse
from django.utils.html import format_html
from .models import CustomUser

class ESCOAdminSite(AdminSite):
    site_header = "ESCO Administration"
    site_title = "ESCO Admin"
    index_title = "Panneau d'administration ESCO"
    
    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['custom_dashboard_url'] = reverse('dashboard_admin')
        return super().index(request, extra_context)

# Créez une instance personnalisée
esco_admin_site = ESCOAdminSite(name='esco_admin')

# Enregistrez vos modèles
esco_admin_site.register(CustomUser)
# accounts/urls.py

from django.urls import path, include
from .views import SignUpView

urlpatterns = [
    # Usamos las vistas de autenticación que vienen con Django
    # para login, logout, cambio de contraseña, etc.
    path('', include('django.contrib.auth.urls')),
    
    # Nuestra vista personalizada para el registro
    path('signup/', SignUpView.as_view(), name='signup'),
]
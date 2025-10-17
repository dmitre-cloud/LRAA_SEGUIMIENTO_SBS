from django.shortcuts import render

# Create your views here.
# accounts/views.py

from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import CustomUserCreationForm

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    # Cuando el registro es exitoso, redirige al usuario a la página de login
    success_url = reverse_lazy('login') 
    template_name = 'registration/signup.html'
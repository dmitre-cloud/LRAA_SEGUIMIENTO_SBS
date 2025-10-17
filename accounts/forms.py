# accounts/forms.py

from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        # Añade aquí todos los campos que quieres en el formulario de registro
        fields = ('username', 'first_name', 'last_name', 'email', 'department', 'job_position', 'phone')
    
    # AÑADE ESTE MÉTODO PARA APLICAR LOS ESTILOS
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Agrega la clase 'form-control' a todos los campos
            field.widget.attrs['class'] = 'form-control'
            # Haz que el campo de email no sea requerido si lo deseas
            if field_name == 'email':
                field.required = False

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        # Campos que un usuario puede editar en su perfil
        fields = ('username', 'first_name', 'last_name', 'email', 'department', 'job_position', 'phone')
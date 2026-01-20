from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
class CustomUser(AbstractUser):
    # Opciones para el menú desplegable (ComboBox)
    DEPARTAMENTO_CHOICES = [
        ('Química', 'Química'),
        ('Microbiología', 'Microbiología'),
        ('Dirección', 'Dirección'),
        ('Proyecto de equipamiento', 'Proyecto de equipamiento'),
        # Puedes agregar más si es necesario
    ]

    # Añadimos el atributo 'choices' al campo department
    department = models.CharField(max_length=50, blank=False, choices=DEPARTAMENTO_CHOICES,verbose_name="Departamento")
    job_position = models.CharField(max_length=80, blank=True,verbose_name="Posición o cargo de trabajo")
    phone = models.CharField(max_length=25, blank=True,verbose_name="Teléfono")
    REQUIRED_FIELDS = ["first_name","last_name","department"]
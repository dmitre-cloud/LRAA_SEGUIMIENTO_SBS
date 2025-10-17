from django.db import models

# Create your models here.
# solicitudes/models.py

from django.db import models
from django.conf import settings # Para referenciar al CustomUser de forma segura

# Asumo que tu CustomUser está en una app llamada 'accounts'
# from accounts.models import CustomUser 

# --- Modelo para los campos en Rojo ---
class Solicitud(models.Model):
    """
    Representa la solicitud inicial de un bien o servicio hecha por un departamento.
    """
    DEPARTAMENTO_CHOICES = [
        ('Química', 'Química'),
        ('Microbiología', 'Microbiología'),
        ('Dirección', 'Dirección'),
        ('Proyecto de equipamiento', 'Proyecto de equipamiento'),
        # Agrega más departamentos si es necesario
    ]

    TIPO_COMPRA_CHOICES = [
        ('Bien', 'Bien'),
        ('Servicio', 'Servicio'),
    ]

    # Relación con el usuario que crea la solicitud
    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='solicitudes'
    )
    
    departamento = models.CharField(
        max_length=50, 
        choices=DEPARTAMENTO_CHOICES,
        help_text="El departamento que hace la solicitud"
    )
    ref_departamento = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Identificación de cada departamento (M, Q, D, E)"
    )
    descripcion_pedido = models.TextField(
        help_text="Descripción general del pedido (SBS)"
    )
    monto_comprometido_sbs = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Monto total de la SBS enviada a presupuesto"
    )
    tipo_compra = models.CharField(
        max_length=10, 
        choices=TIPO_COMPRA_CHOICES,
        help_text="Si la SBS es un bien o un servicio"
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"SBS-{self.id} | {self.descripcion_pedido[:50]}..."

    class Meta:
        verbose_name = "Solicitud de Bien o Servicio"
        verbose_name_plural = "Solicitudes de Bienes y Servicios"
        ordering = ['-fecha_creacion']


# --- Modelo para los campos en Negro ---
class SeguimientoCompra(models.Model):
    """
    Representa el seguimiento, la orden de compra y la recepción de una Solicitud.
    """
    CONDICION_CHOICES = [
        ('recorrido', 'En Recorrido'),
        ('ingresado_v3', 'Ingresado al V3'),
        ('evaluado', 'Evaluado'),
        ('refrendado', 'Refrendado'),
        ('anulado', 'Anulado'),
        ('finalizado', 'Finalizado'),
    ]
    TIPO_ENTREGA_CHOICES = [
        ('Total', 'Total'),
        ('Parcial', 'Parcial'),
    ]
    TIPO_PLAZO_CHOICES = [
        ('Calendario', 'Días Calendario'),
        ('Habiles', 'Días Hábiles'),
    ]
    STATUS_FINAL_CHOICES = [
        ('Entregado', 'Entregado'),
        ('Realizado', 'Realizado'),
        ('Pendiente', 'Pendiente'),
        ('Por Entregar', 'Por Entregar'),
    ]

    # Relación uno a uno con la solicitud original. Cada solicitud tiene un único seguimiento.
    solicitud = models.OneToOneField(
        Solicitud, 
        on_delete=models.CASCADE, 
        related_name='seguimiento'
    )

    # Campos del seguimiento
    numero_partida = models.CharField(max_length=100, blank=True)
    condicion = models.CharField(max_length=20, choices=CONDICION_CHOICES, default='recorrido')
    fecha_ingreso_v3 = models.DateField(null=True, blank=True)
    sbs_numero = models.CharField(max_length=50, blank=True, help_text="Número de la solicitud de bienes y servicios (###-2026)")
    fecha_pedido_evaluado = models.DateField(null=True, blank=True)
    oc_numero = models.CharField(max_length=100, blank=True, help_text="Número de la Orden de Compra (4200#######)")
    fecha_publicacion_oc = models.DateField(null=True, blank=True)
    monto_oc = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tipo_entrega = models.CharField(max_length=10, choices=TIPO_ENTREGA_CHOICES, blank=True)
    plazo_entrega = models.PositiveIntegerField(null=True, blank=True, help_text="Días para realizar la entrega")
    tipo_plazo = models.CharField(max_length=15, choices=TIPO_PLAZO_CHOICES, blank=True)
    vencimiento_oc = models.DateField(null=True, blank=True)
    proveedor = models.CharField(max_length=256, blank=True)
    solicitud_ajuste = models.TextField(blank=True)
    numero_ajuste = models.CharField(max_length=50, blank=True)
    nuevo_plazo_entrega = models.DateField(null=True, blank=True)
    status_final_compra = models.CharField(max_length=20, choices=STATUS_FINAL_CHOICES, blank=True)
    fecha_recibo = models.DateField(null=True, blank=True)
    quien_recibe_almacen = models.CharField(max_length=256, blank=True, help_text="Nombre del que recibe el bien o # de Recibido Conforme")
    observacion_1 = models.TextField(blank=True)
    observacion_2 = models.TextField(blank=True)
    
    # Checkboxes
    mantenimiento = models.BooleanField(default=False)
    calibracion = models.BooleanField(default=False)
    caracterizacion = models.BooleanField(default=False)
    
    # Fechas adicionales
    fecha_inicial_mant_calib_caract = models.DateField(null=True, blank=True)
    fecha_final_mant_calib_caract = models.DateField(null=True, blank=True)
    
    # Enlaces
    enlace_orden_compra = models.URLField(max_length=500, blank=True)
    enlace_sbs = models.URLField(max_length=500, blank=True)
    
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Seguimiento de SBS-{self.solicitud.id}"

    class Meta:
        verbose_name = "Seguimiento de Compra"
        verbose_name_plural = "Seguimientos de Compras"
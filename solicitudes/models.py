from django.db import models
from django.conf import settings # Para referenciar al CustomUser de forma segura
from datetime import date, datetime, timedelta # Importamos timedelta para cálculos de fechas

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

    URGENTE_CHOICES = [
        ('Aplica', 'Aplica'),
        ('No Aplica', 'No Aplica'),
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

    urgente = models.CharField(
        max_length=10,
        choices=URGENTE_CHOICES,
        default='No Aplica',
        help_text="Indique si la solicitud requiere trámite urgente"
    )

    ref_departamento = models.CharField(
        max_length=100, 
        blank=True,
        editable=False, # 👈 IMPORTANTE: Esto evita que se muestre en el admin o forms por defecto
        help_text="Identificación automática (Ej: M-01-25)"
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

    # --- LÓGICA DE GENERACIÓN DE CÓDIGO ---
    def save(self, *args, **kwargs):
        # Solo generamos si es nuevo o no tiene referencia
        if not self.ref_departamento:
            self.generar_codigo_referencia()
        super(Solicitud, self).save(*args, **kwargs)

    def generar_codigo_referencia(self):
        """Genera el código consecutivo tipo DEP-###-AAAA"""
        
        # 1. Prefijos
        prefijos = {
            'Química': 'Q',
            'Microbiología': 'M',
            'Dirección': 'D',
            'Proyecto de equipamiento': 'PE', 
        }
        prefijo = prefijos.get(self.departamento, 'GEN')
        
        # 2. Año actual de 4 dígitos (Ej: 2025)
        anio_actual = datetime.now().strftime('%Y')
        
        # 3. Buscar último consecutivo de este año y departamento
        ultima_solicitud = Solicitud.objects.filter(
            departamento=self.departamento,
            ref_departamento__endswith=f"-{anio_actual}"
        ).order_by('id').last()

        if ultima_solicitud and ultima_solicitud.ref_departamento:
            try:
                # ref: "M-05-2025" -> split -> ["M", "05", "2025"]
                partes = ultima_solicitud.ref_departamento.split('-')
                consecutivo_anterior = int(partes[1])
                nuevo_consecutivo = consecutivo_anterior + 1
            except (IndexError, ValueError):
                nuevo_consecutivo = 1
        else:
            nuevo_consecutivo = 1

        # 4. Asignar formato
        self.ref_departamento = f"{prefijo}-{nuevo_consecutivo:02d}-{anio_actual}"

    def __str__(self):
        return f"{self.ref_departamento} | {self.descripcion_pedido[:50]}..."

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
        ('OC - POR ENTREGAR', 'OC - POR ENTREGAR'),
        ('OC - ENTREGADA ***(ENTREGA TOTAL)*** COMPLETADA.', 'OC - ENTREGADA ***(ENTREGA TOTAL)*** COMPLETADA.'),
        ('OC - PENDIENTE POR ENTREGAR ***(ENTREGA PARCIAL):*** Próxima a completarse.', 'OC - PENDIENTE POR ENTREGAR ***(ENTREGA PARCIAL):*** Próxima a completarse.'),
        ('OC - SERVICIO REALIZADO ***(ENTREGA TOTAL)***COMPLETADA.', 'OC - SERVICIO REALIZADO ***(ENTREGA TOTAL)***COMPLETADA.'),
        ('OC - SERVICIO PENDIENTE POR REALIZAR (ENTREGA PARCIAL ):*** Próxima a completarse.', 'OC - SERVICIO PENDIENTE POR REALIZAR (ENTREGA PARCIAL ):*** Próxima a completarse.'),
        ('OC - ***PARCIAL FINALIZADO***', 'OC - ***PARCIAL FINALIZADO***'),
    ]
    
    # Relación uno a uno con la solicitud original. Cada solicitud tiene un único seguimiento.
    solicitud = models.OneToOneField(
        Solicitud, 
        on_delete=models.CASCADE, 
        related_name='seguimiento'
    )
    def get_condiciones_list(self):
        """Retorna una lista de diccionarios con el código y la etiqueta para el listado"""
        if not self.condicion:
            return []
        
        # Diccionario para buscar etiquetas rápidamente
        choices_dict = dict(self.CONDICION_CHOICES)
        codigos = self.condicion.split(',')
        
        return [
            {'codigo': c, 'label': choices_dict.get(c, c)} 
            for c in codigos
        ]
        
    # Campos del seguimiento
    numero_partida = models.CharField(max_length=100, blank=True, verbose_name="NÚMERO DE PARTIDA")
    condicion = models.CharField(max_length=255, blank=True, verbose_name="CONDICIÓN")
    fecha_ingreso_v3 = models.DateField(null=True, blank=True, verbose_name="FECHA DE INGRESO AL V3")
    sbs_numero = models.CharField(max_length=50, blank=True, verbose_name="NÚMERO DE SBS")
    
    # --- NUEVOS CAMPOS ---
    enlace_evaluacion = models.URLField(max_length=500, blank=True, verbose_name="ENLACE DE EVALUACIÓN")
    enlace_recibido_conforme = models.URLField(max_length=500, blank=True, verbose_name="ENLACE DE RECIBIDO CONFORME")
    numero_recibido_conforme = models.TextField(blank=True, verbose_name="NÚMERO DE RECIBIDO CONFORME")
    observacion_ajuste = models.TextField(blank=True, verbose_name="OBSERVACIÓN DEL AJUSTE")
    # ---------------------
    
    fecha_pedido_evaluado = models.DateField(null=True, blank=True, verbose_name="FECHA DE PEDIDO EVALUADO")
    oc_numero = models.CharField(max_length=100, blank=True, verbose_name="NÚMERO DE LA ORDEN DE COMPRA")
    fecha_publicacion_oc = models.DateField(null=True, blank=True, verbose_name="FECHA DE PUBLICACIÓN DE LA ORDEN DE COMPRA")
    monto_oc = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="MONTO DE LA ORDEN DE COMPRA")
    tipo_entrega = models.CharField(max_length=10, choices=TIPO_ENTREGA_CHOICES, blank=True, verbose_name="TIPO DE ENTREGA")
    plazo_entrega = models.PositiveIntegerField(null=True, blank=True, verbose_name="PLAZO DE ENTREGA")
    tipo_plazo = models.CharField(max_length=15, choices=TIPO_PLAZO_CHOICES, blank=True, verbose_name="TIPO DE PLAZO")
    vencimiento_oc = models.DateField(null=True, blank=True, verbose_name="VENCIMIENTO DE LA ORDEN DE COMPRA")
    proveedor = models.CharField(max_length=256, blank=True, verbose_name="PROVEEDOR")
    solicitud_ajuste = models.TextField(blank=True, verbose_name="SOLICITUD DE AJUSTE")
    numero_ajuste = models.CharField(max_length=50, blank=True, verbose_name="NÚMERO DE AJUSTE")
    nuevo_plazo_entrega = models.DateField(null=True, blank=True, verbose_name="NUEVO PLAZO DE ENTREGA")
    status_final_compra = models.CharField(max_length=100, choices=STATUS_FINAL_CHOICES, blank=True, verbose_name="ESTADO FINAL DE LA COMPRA")
    fecha_recibo = models.DateField(null=True, blank=True, verbose_name="FECHA DE RECIBIDO EN ALMACÉN")
    
    # Modificado para que sea cuadro de observación según tu diseño
    quien_recibe_almacen = models.TextField(blank=True, verbose_name="QUIÉN RECIBE EN ALMACÉN") 
    
    observacion_1 = models.TextField(blank=True, verbose_name="OBSERVACIÓN 1")
    observacion_2 = models.TextField(blank=True, verbose_name="OBSERVACIÓN 2")
    
    # Checkboxes
    mantenimiento = models.BooleanField(default=False, verbose_name="MANTENIMIENTO")
    calibracion = models.BooleanField(default=False, verbose_name="CALIBRACIÓN")
    caracterizacion = models.BooleanField(default=False, verbose_name="CARACTERIZACIÓN")
    
    fecha_inicial_mant_calib_caract = models.DateField(null=True, blank=True, verbose_name="FECHA INICIAL DEL SERVICIO")
    
    # Enlaces
    enlace_orden_compra = models.URLField(max_length=500, blank=True, verbose_name="ENLACE DE LA ORDEN DE COMPRA")
    enlace_sbs = models.URLField(max_length=500, blank=True, verbose_name="ENLACE DE LA SBS INGRESADA AL V3")
    
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
# --- MÉTODOS DE FECHA ACTUALIZADOS ---
    def _obtener_feriados_panama(self, anio):
        """Genera el conjunto de feriados nacionales oficiales de Panamá para un año dado"""
        feriados = set()
        
        # 1. Feriados Fijos Nacionales
        feriados_fijos = [
            (1, 1),   # Año Nuevo
            (1, 9),   # Día de los Mártires
            (5, 1),   # Día del Trabajo
            (11, 3),  # Separación de Panamá de Colombia
            (11, 5),  # Consolidación de la Separación en Colón (Feriado institucional/público)
            (11, 10), # Grito de Independencia en la Villa de Los Santos
            (11, 28), # Independencia de Panamá de España
            (12, 8),  # Día de la Madre
            (12, 20), # Día de Duelo Nacional (Invasión de 1989)
            (12, 25), # Navidad
        ]
        
        for mes, dia in feriados_fijos:
            fecha_feriado = date(anio, mes, dia)
            feriados.add(fecha_feriado)
            # Regla de Puente: Si cae Domingo (6), se traslada el descanso al Lunes (+1 día)
            if fecha_feriado.weekday() == 6:
                feriados.add(fecha_feriado + timedelta(days=1))
                
        # 2. Feriados Variables (Algoritmo de Meeus/Jones/Butcher para Domingo de Pascua)
        a = anio % 19
        b = anio // 100
        c = anio % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        L = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * L) // 451
        mes_pascua = (h + L - 7 * m + 114) // 31
        dia_pascua = ((h + L - 7 * m + 114) % 31) + 1
        
        pascua = date(anio, mes_pascua, dia_pascua)
        
        # Calcular días dependientes de la Pascua
        viernes_santo = pascua - timedelta(days=2)
        martes_carnaval = pascua - timedelta(days=47)
        lunes_carnaval = pascua - timedelta(days=48) # Tradicionalmente libre en sector público
        
        feriados.add(viernes_santo)
        feriados.add(martes_carnaval)
        feriados.add(lunes_carnaval)
        
        return feriados

    def _agregar_dias_habiles(self, fecha_inicial, dias):
        if not isinstance(fecha_inicial, date): return None
        if dias <= 0: return fecha_inicial
        
        dias_agregados = 0
        fecha_actual = fecha_inicial
        feriados_cache = {} # Cache para evitar recálculos si salta de un año a otro
        
        while dias_agregados < dias:
            fecha_actual += timedelta(days=1)
            anio_actual = fecha_actual.year
            
            if anio_actual not in feriados_cache:
                feriados_cache[anio_actual] = self._obtener_feriados_panama(anio_actual)
                
            # Es día hábil si es de Lunes a Viernes Y NO está en el set de feriados
            if fecha_actual.weekday() < 5 and fecha_actual not in feriados_cache[anio_actual]:
                dias_agregados += 1
                
        return fecha_actual

    def _agregar_dias_calendario(self, fecha_inicial, dias):
        if not isinstance(fecha_inicial, date): return None
        if dias < 0: dias = 0
        return fecha_inicial + timedelta(days=dias)

    def save(self, *args, **kwargs):
        if self.fecha_publicacion_oc and self.plazo_entrega is not None and self.tipo_plazo:
            try:
                # Al actualizar '_agregar_dias_habiles', los 2 días base ya omitirán fines de semana y feriados de Panamá automáticamente
                fecha_con_dias_base = self._agregar_dias_habiles(self.fecha_publicacion_oc, 2)
                if self.tipo_plazo == 'Habiles':
                    self.vencimiento_oc = self._agregar_dias_habiles(fecha_con_dias_base, self.plazo_entrega)
                elif self.tipo_plazo == 'Calendario':
                    self.vencimiento_oc = self._agregar_dias_calendario(fecha_con_dias_base, self.plazo_entrega)
            except Exception:
                pass
        super(SeguimientoCompra, self).save(*args, **kwargs)

    def __str__(self):
        return f"Seguimiento de {self.solicitud}"

    class Meta:
        verbose_name = "Seguimiento de Compra"
        verbose_name_plural = "Seguimientos de Compras"
    
    def get_condicion_color(self):
        """Retorna el color de Bootstrap según el estado"""
        colores = {
            'recorrido': 'warning text-dark', # Amarillo
            'ingresado_v3': 'primary',       # Azul
            'evaluado': 'info text-dark',    # Celeste
            'refrendado': 'success',         # Verde
            'anulado': 'danger',             # Rojo
            'finalizado': 'dark',            # Negro/Gris oscuro
        }
        # Retorna el color o 'secondary' si no encuentra el estado
        return colores.get(self.condicion, 'secondary')
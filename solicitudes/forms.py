from django import forms
from .models import Solicitud, SeguimientoCompra

class SolicitudForm(forms.ModelForm):
    # ... (este formulario no necesita cambios)
    class Meta:
        model = Solicitud
        # El campo 'urgente' se incluirá automáticamente al no estar en exclude
        # 👈 AGREGAMOS 'ref_departamento' a la lista de excluidos
        exclude = ('solicitante', 'ref_departamento') 
        widgets = {
            'descripcion_pedido': forms.Textarea(attrs={'rows': 7}),
            'monto_comprometido_sbs': forms.NumberInput(attrs={'placeholder': 'Ej: 1500.50'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Esto asignará 'form-select' automáticamente a nuestro nuevo campo 'urgente'
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            elif not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-control'


class SeguimientoCompraForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        roles_permitidos = ['Asistente Administrativo', 'Director Encargado']
        can_edit = user and user.job_position in roles_permitidos
        
        for field_name, field in self.fields.items():
            current_classes = field.widget.attrs.get('class', '')
            
            # --- 1. Aplicación de Clases Base de Bootstrap ---
            if isinstance(field.widget, forms.CheckboxInput):
                if 'form-check-input' not in current_classes:
                    field.widget.attrs['class'] = (current_classes + ' form-check-input').strip()
            
            # NUEVO: Evitamos aplicar form-control a los RadioSelect para que se vean bien en línea
            elif isinstance(field.widget, forms.RadioSelect):
                pass 
                
            elif isinstance(field.widget, forms.Select):
                if 'form-select' not in current_classes:
                    field.widget.attrs['class'] = (current_classes + ' form-select').strip()
            else:
                if 'form-control' not in current_classes:
                    field.widget.attrs['class'] = (current_classes + ' form-control').strip()

            # --- 2. Aplicación de Restricciones ---
            if not can_edit:
                if isinstance(field.widget, (forms.CheckboxInput, forms.RadioSelect)):
                    field.widget.attrs['disabled'] = True
                else:
                    field.widget.attrs['readonly'] = True
                    current_classes = field.widget.attrs.get('class', '')
                    if 'bg-light' not in current_classes:
                        field.widget.attrs['class'] = (current_classes + ' bg-light').strip()

    class Meta:
        model = SeguimientoCompra
        exclude = ('solicitud', 'observacion_1', 'observacion_2', 'fecha_inicial_mant_calib_caract') # Excluimos los que no están en el diseño
        
        widgets = {
            'condicion': forms.RadioSelect(), # <-- Agregado para que sea de selección múltiple horizontal
            'plazo_entrega': forms.NumberInput(attrs={'id': 'id_plazo_entrega'}),
            'tipo_plazo': forms.Select(attrs={'id': 'id_tipo_plazo_entrega'}),
            'fecha_publicacion_oc': forms.DateInput(attrs={'type': 'date', 'id': 'id_fecha_publicacion_oc'}, format='%Y-%m-%d'),
            'vencimiento_oc': forms.DateInput(
                attrs={'type': 'date', 'id': 'id_vencimiento_oc', 'readonly': True}, 
                format='%Y-%m-%d'
            ),
            'fecha_ingreso_v3': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'fecha_pedido_evaluado': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'nuevo_plazo_entrega': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'fecha_recibo': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            
            # Cuadros de observación (Textareas) según el diseño
            'quien_recibe_almacen': forms.Textarea(attrs={'rows': 2}),
            'numero_recibido_conforme': forms.Textarea(attrs={'rows': 2}),
            'solicitud_ajuste': forms.Textarea(attrs={'rows': 2}),
            'observacion_ajuste': forms.Textarea(attrs={'rows': 2}),
        }


# --- AGREGA ESTA NUEVA CLASE AL FINAL DEL ARCHIVO ---
class SeguimientoFilterForm(forms.Form):
    """
    Este formulario no guarda datos, solo se usa para validar y limpiar
    los parámetros de búsqueda que llegan por GET en la vista de reportes.
    """
    # Traemos las opciones desde el modelo y añadimos una opción vacía para "Todos"
    CONDICION_CHOICES = [('', '---------')] + SeguimientoCompra.CONDICION_CHOICES
    STATUS_CHOICES = [('', '---------')] + SeguimientoCompra.STATUS_FINAL_CHOICES
    TIPO_COMPRA_CHOICES = [('', '---------')] + Solicitud.TIPO_COMPRA_CHOICES
    
    sbs_numero = forms.CharField(
        required=False,
        label="N° SBS",
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Ej: 001-2026'})
    )
    oc_numero = forms.CharField(
        required=False,
        label="N° OC",
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Ej: 4200...'})
    )
    
    condicion = forms.ChoiceField(
        choices=CONDICION_CHOICES,
        required=False,
        label="Condición",
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    status_final_compra = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        label="Status",
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    tipo_compra = forms.ChoiceField(
        choices=TIPO_COMPRA_CHOICES,
        required=False,
        label="Tipo de Compra",
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    proveedor = forms.CharField(
        required=False,
        label="Proveedor",
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Nombre del proveedor'})
    )
    # 🌟 NUEVO CAMPO PARA FILTRAR POR AÑO
    anio = forms.IntegerField(
        required=False,
        label="Año",
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Ej: 2025', 'min': '2020'})
    )
    # 👇 AGREGA ESTE NUEVO CAMPO
    ref_departamento = forms.CharField(
        required=False,
        label="Código / Ref.",
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Ej: M-01-2025'})
    )
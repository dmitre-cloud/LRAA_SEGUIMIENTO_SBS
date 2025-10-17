# solicitudes/forms.py

from django import forms
from .models import Solicitud, SeguimientoCompra

class SolicitudForm(forms.ModelForm):
    class Meta:
        model = Solicitud
        # Excluimos el solicitante porque se asignará automáticamente en la vista
        exclude = ('solicitante',) 
        widgets = {
            'descripcion_pedido': forms.Textarea(attrs={'rows': 3}),
            'monto_comprometido_sbs': forms.NumberInput(attrs={'placeholder': 'Ej: 1500.50'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class SeguimientoCompraForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        is_admin_assistant = user and user.job_position == 'Asistente Administrativo'
        
        # Lógica para aplicar clases y estado readonly/disabled
        for field_name, field in self.fields.items():
            # Aplicar clases de Bootstrap
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'
            
            # **CORRECCIÓN 1: Usar 'readonly' en lugar de 'disabled'**
            # Esto permite que JavaScript escriba en el campo y que el valor se guarde.
            if not is_admin_assistant:
                field.widget.attrs['readonly'] = True
                # Opcional: añade un fondo gris para que se vea como deshabilitado
                if not isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs['class'] += ' bg-light'
                    

    class Meta:
        model = SeguimientoCompra
        exclude = ('solicitud',)
        
        widgets = {
            # **CORRECCIÓN 2: Añadir los 'id' para que JavaScript los encuentre**
            'plazo_entrega': forms.NumberInput(
                # Django por defecto crearía un id="id_plazo_entrega", pero es mejor ser explícito.
                attrs={'id': 'id_plazo_entrega'}
            ),
            'fecha_publicacion_oc': forms.DateInput(
                attrs={'type': 'date', 'id': 'id_fecha_publicacion_oc'}, 
                format='%Y-%m-%d'
            ),
            'vencimiento_oc': forms.DateInput(
                attrs={
                    'type': 'date',
                    'id': 'id_vencimiento_oc',
                    # Aseguramos que sea solo lectura para que el usuario no lo cambie
                    'readonly': True 
                }, 
                format='%Y-%m-%d'
            ),
            
            # --- El resto de tus widgets permanecen igual ---
            'fecha_ingreso_v3': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'fecha_pedido_evaluado': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'nuevo_plazo_entrega': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'fecha_recibo': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'fecha_inicial_mant_calib_caract': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'fecha_final_mant_calib_caract': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'observacion_1': forms.Textarea(attrs={'rows': 2}),
            'observacion_2': forms.Textarea(attrs={'rows': 2}),
            'solicitud_ajuste': forms.Textarea(attrs={'rows': 2}),
        }
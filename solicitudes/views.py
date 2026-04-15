# solicitudes/views.py
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Sum

from .models import Solicitud, SeguimientoCompra
from .forms import SolicitudForm, SeguimientoCompraForm, SeguimientoFilterForm

# --- Vistas para Solicitud ---
from django.db.models import Q

class SolicitudListView(LoginRequiredMixin, ListView):
    model = Solicitud
    template_name = 'solicitudes/solicitud_list.html'
    context_object_name = 'solicitudes'
    paginate_by = 5
    ordering = ['-id']

    def get_queryset(self):
        user = self.request.user
        # Optimizamos con select_related('seguimiento')
        queryset = super().get_queryset().select_related('seguimiento')

        # --- Lógica de Permisos ---
        job_position_con_acceso_total = ['Asistente Administrativo']
        departamentos_con_acceso_total = ['Dirección']

        if user.job_position not in job_position_con_acceso_total and user.department not in departamentos_con_acceso_total:
            queryset = queryset.filter(departamento=user.department)

        # --- Lógica de Búsqueda ---
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(descripcion_pedido__icontains=query) | 
                Q(ref_departamento__icontains=query) |
                # OPCIONAL: Permitir buscar también por número de SBS
                Q(seguimiento__sbs_numero__icontains=query) 
            )
        
        return queryset

class SolicitudDetailView(LoginRequiredMixin, DetailView):
    model = Solicitud
    template_name = 'solicitudes/solicitud_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        solicitud = self.get_object()
        seguimiento, created = SeguimientoCompra.objects.get_or_create(solicitud=solicitud)
        
        # Le pasamos el request.user al formulario al instanciarlo
        context['seguimiento_form'] = SeguimientoCompraForm(
            instance=seguimiento, 
            user=self.request.user
        )
        
        context['seguimiento'] = seguimiento
        return context

class SolicitudCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView): # 🌟 IMPORTANTE: Añadir UserPassesTestMixin aquí para usar test_func 🌟
    model = Solicitud
    form_class = SolicitudForm
    template_name = 'solicitudes/solicitud_form.html'
    success_url = reverse_lazy('solicitud-list')

    def test_func(self):
        # ✅ CORRECCIÓN: Permitir la creación al Asistente Administrativo y a cualquier otro.
        # Dado que está dentro de LoginRequiredMixin, el usuario ya está autenticado.
        # Si quieres restringir la creación a 'Asistente Administrativo' y otros cargos específicos,
        # deberías definir esa lógica. Si no, solo devuelve True.
        # Por simplicidad, asumiremos que si ya puede verlo (por SolicitudListView) puede crearlo,
        # pero también lo forzamos a pasar la validación por si acaso.
        # Opción 1 (Más flexible): return True 
        # Opción 2 (Restringida, si quieres que solo Asistente Administrativo y otros específicos creen):
        # return self.request.user.job_position in ['Asistente Administrativo', 'Director', 'Otro Cargo']
        
        # Dejamos 'True' para permitir la creación a todos los logueados, a menos que haya una restricción específica no mencionada.
        return True 

    def form_valid(self, form):
        form.instance.solicitante = self.request.user
        return super().form_valid(form)

class SolicitudUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Solicitud
    form_class = SolicitudForm
    template_name = 'solicitudes/solicitud_form.html'
    success_url = reverse_lazy('solicitud-list')

    def test_func(self):
        solicitud = self.get_object()
        user = self.request.user
        
        # ✅ CORRECCIÓN: Permitir la edición si es el creador O si tiene el cargo de 'Asistente Administrativo'
        # Esto permite que el creador (sin importar su cargo) edite, Y que el Asistente Administrativo edite cualquiera.
        es_asistente_administrativo = user.job_position == 'Asistente Administrativo'
        es_el_solicitante = solicitud.solicitante == user

        # Puede editar si es el solicitante O si es Asistente Administrativo
        return es_el_solicitante or es_asistente_administrativo

# --- VISTA DE ELIMINACIÓN ---

class SolicitudDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Solicitud
    template_name = 'solicitudes/solicitud_confirm_delete.html'
    success_url = reverse_lazy('solicitud-list')

    def test_func(self):
        """
        Verifica que el usuario pueda eliminar la solicitud.
        """
        solicitud = self.get_object()
        user = self.request.user
        
        # ✅ CORRECCIÓN: Permitir la eliminación si es el creador O si tiene el cargo de 'Asistente Administrativo'
        es_asistente_administrativo = user.job_position == 'Asistente Administrativo'
        es_el_solicitante = solicitud.solicitante == user
        
        # Puede eliminar si es el solicitante O si es Asistente Administrativo
        return es_el_solicitante or es_asistente_administrativo

# --- Vista para actualizar el Seguimiento ---
# ... (El resto del código de SeguimientoUpdateView, SeguimientoReportView, etc., se mantiene igual ya que no se necesita modificación
# para el requisito de CRUD de Solicitud)
# Si el Asistente Administrativo necesita permisos especiales en SeguimientoUpdateView, también deberías revisar esa vista.

class SeguimientoUpdateView(LoginRequiredMixin, UpdateView):
    model = SeguimientoCompra
    form_class = SeguimientoCompraForm
    template_name = 'solicitudes/seguimiento_form.html' # Puedes crear una plantilla específica si lo deseas

    def get_object(self, queryset=None):
        # Obtenemos el seguimiento a partir del PK de la solicitud
        solicitud_pk = self.kwargs.get('solicitud_pk')
        solicitud = get_object_or_404(Solicitud, pk=solicitud_pk)
        seguimiento, created = SeguimientoCompra.objects.get_or_create(solicitud=solicitud)
        return seguimiento

    def get_success_url(self):
        # Redirige de vuelta al detalle de la solicitud después de actualizar
        return reverse_lazy('solicitud-detail', kwargs={'pk': self.object.solicitud.pk})


class SeguimientoReportView(LoginRequiredMixin, ListView):
    model = SeguimientoCompra
    template_name = 'solicitudes/seguimiento_report.html'
    context_object_name = 'seguimientos'
    paginate_by = 10

    def get_paginate_by(self, queryset):
        """
        Si detecta el parámetro 'print' en la URL, desactiva la paginación
        devolviendo None. De lo contrario, usa el valor por defecto (10).
        """
        if self.request.GET.get('print'):
            return None
        return self.paginate_by

    def get_queryset(self):
        """
        Este método aplica los permisos de departamento y los filtros de búsqueda.
        """
        user = self.request.user
        queryset = SeguimientoCompra.objects.select_related('solicitud').all()

        cargos_con_acceso_total = ['Asistente Administrativo', 'Director Encargado']
        if user.job_position not in cargos_con_acceso_total:
            queryset = queryset.filter(solicitud__departamento=user.department)

        self.filter_form = SeguimientoFilterForm(self.request.GET)
        if self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data

            if cleaned_data.get('sbs_numero'):
                queryset = queryset.filter(sbs_numero__icontains=cleaned_data['sbs_numero'])
        
            if cleaned_data.get('oc_numero'):
                queryset = queryset.filter(oc_numero__icontains=cleaned_data['oc_numero'])

            if cleaned_data.get('condicion'):
                queryset = queryset.filter(condicion=cleaned_data['condicion'])
            if cleaned_data.get('status_final_compra'):
                queryset = queryset.filter(status_final_compra=cleaned_data['status_final_compra'])
            if cleaned_data.get('tipo_compra'):
                queryset = queryset.filter(solicitud__tipo_compra=cleaned_data['tipo_compra'])
            if cleaned_data.get('proveedor'):
                queryset = queryset.filter(proveedor__icontains=cleaned_data['proveedor'])
            
            # Lógica de filtro por año
            if cleaned_data.get('anio'):
                queryset = queryset.filter(solicitud__fecha_creacion__year=cleaned_data['anio'])
            
            # Filtro por referencia
            if cleaned_data.get('ref_departamento'):
                queryset = queryset.filter(solicitud__ref_departamento__icontains=cleaned_data['ref_departamento'])
        
        return queryset.order_by('-solicitud__fecha_creacion')

    def get_context_data(self, **kwargs):
        """
        Añadimos el formulario de filtros y el total del Monto OC al contexto.
        """
        context = super().get_context_data(**kwargs)
        context['filter_form'] = self.filter_form
        
        # --- 👇 AJUSTE PARA EL TOTAL 👇 ---
        # Calculamos el total sobre el queryset completo filtrado (get_queryset),
        # no sobre self.object_list, para que el total sea global aunque haya paginación.
        filtered_queryset = self.get_queryset()
        total_monto_oc = filtered_queryset.aggregate(total=Sum('monto_oc'))['total'] or 0.00
        context['total_monto_oc'] = total_monto_oc
        # --- 👆 FIN DEL AJUSTE ---

        return context
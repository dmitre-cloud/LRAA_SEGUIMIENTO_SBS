from django.shortcuts import render

# Create your views here.
# solicitudes/views.py

from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Solicitud, SeguimientoCompra
from .forms import SolicitudForm, SeguimientoCompraForm
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# --- Vistas para Solicitud ---

class SolicitudListView(LoginRequiredMixin, ListView):
    model = Solicitud
    template_name = 'solicitudes/solicitud_list.html'
    context_object_name = 'solicitudes'
    paginate_by = 10

    def get_queryset(self):
        """
        Sobrescribe el queryset original para filtrar por departamento.
        """
        user = self.request.user
        queryset = super().get_queryset() # Obtiene el queryset base: Solicitud.objects.all()

        # Define los roles o departamentos con acceso total
        job_position_con_acceso_total = ['Asistente Administrativo']
        departamentos_con_acceso_total = ['Dirección']

        # Si el departamento del usuario NO es 'Dirección', filtra las solicitudes
        # que coinciden con el departamento del usuario.
        # Si el usuario NO pertenece a los grupos con acceso total, filtra por su departamento
        if user.job_position not in job_position_con_acceso_total and user.department not in departamentos_con_acceso_total:
            queryset = queryset.filter(departamento=user.department)
        
        # El usuario de 'Dirección' recibirá el queryset sin filtrar (todas las solicitudes)
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

class SolicitudCreateView(LoginRequiredMixin, CreateView):
    model = Solicitud
    form_class = SolicitudForm
    template_name = 'solicitudes/solicitud_form.html'
    success_url = reverse_lazy('solicitud-list')

    def test_func(self):
        # El usuario puede crear si su cargo NO es 'Asistente Administrativo'
        return self.request.user.job_position != 'Asistente Administrativo'

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
        # El usuario puede editar si:
        # 1. Es el creador de la solicitud Y
        # 2. Su cargo NO es 'Asistente Administrativo'
        return solicitud.solicitante == user and user.job_position != 'Asistente Administrativo'

# --- VISTA DE ELIMINACIÓN (AQUÍ APLICAMOS LA CORRECCIÓN) ---

class SolicitudDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView): # 1. AÑADIMOS UserPassesTestMixin
    model = Solicitud
    template_name = 'solicitudes/solicitud_confirm_delete.html'
    success_url = reverse_lazy('solicitud-list')

    # 2. AÑADIMOS LA FUNCIÓN DE VALIDACIÓN
    def test_func(self):
        """
        Esta función verifica que el usuario que intenta borrar la solicitud
        sea el mismo que la creó.
        """
        # Obtenemos el objeto de la solicitud que se va a borrar
        solicitud = self.get_object()
        
        # Comparamos el campo 'solicitante' de la solicitud con el usuario logueado
        return solicitud.solicitante == self.request.user

# --- Vista para actualizar el Seguimiento ---

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
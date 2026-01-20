# solicitudes/urls.py

from django.urls import path
from .views import (
    SolicitudListView,
    SolicitudDetailView,
    SolicitudCreateView,
    SolicitudUpdateView,
    SolicitudDeleteView,
    SeguimientoUpdateView,
    SeguimientoReportView,
)

urlpatterns = [
    # URLs para Solicitudes
    path('', SolicitudListView.as_view(), name='solicitud-list'),
        
    path('solicitud/<int:pk>/', SolicitudDetailView.as_view(), name='solicitud-detail'),
    path('solicitud/nueva/', SolicitudCreateView.as_view(), name='solicitud-create'),
    path('solicitud/<int:pk>/editar/', SolicitudUpdateView.as_view(), name='solicitud-update'),
    path('solicitud/<int:pk>/eliminar/', SolicitudDeleteView.as_view(), name='solicitud-delete'),
    
    # URL para el Seguimiento
    path('solicitud/<int:solicitud_pk>/seguimiento/editar/', SeguimientoUpdateView.as_view(), name='seguimiento-update'),
    # --- 2. AÑADE LA NUEVA URL PARA REPORTES ---
    path('reportes/', SeguimientoReportView.as_view(), name='seguimiento-report'),
]
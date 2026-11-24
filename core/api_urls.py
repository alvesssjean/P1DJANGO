from django.urls import path
from . import api_views

urlpatterns = [
    path('tarefas/', api_views.TarefaListCreate.as_view(), name='api_tarefas'),
    path('tarefas/<int:pk>/', api_views.TarefaDetail.as_view(), name='api_tarefa_detalhe'),

    path('projetos/', api_views.ProjetoListCreate.as_view(), name='api_projetos'),
    path('projetos/<int:pk>/', api_views.ProjetoDetail.as_view(), name='api_projeto_detalhe'),

    path('subtarefas/', api_views.SubtarefaListCreate.as_view(), name='api_subtarefas'),
    path('subtarefas/<int:pk>/', api_views.SubtarefaDetail.as_view(), name='api_subtarefa_detalhe'),

    path('dependencias/', api_views.DependenciaListCreate.as_view(), name='api_dependencias'),
    path('dependencias/<int:pk>/', api_views.DependenciaDetail.as_view(), name='api_dependencia_detalhe'),
    path('dashboard/', api_views.DashboardApi.as_view(), name='api_dashboard'),
]
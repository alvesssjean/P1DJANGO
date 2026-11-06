from django.urls import path
from . import api_views

urlpatterns = [
    path('tarefas/', api_views.TarefaListCreate.as_view(), name='api_tarefas'),
    path('tarefas/<int:pk>/', api_views.TarefaDetail.as_view(), name='api_tarefa_detalhe'),
]

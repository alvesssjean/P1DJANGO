from django.urls import path
from .api_views import TarefaListCreate, TarefaDetail

urlpatterns = [
    path('tarefas/', TarefaListCreate.as_view()),
    path('tarefas/<int:pk>/', TarefaDetail.as_view()),
]
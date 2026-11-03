from rest_framework import generics, permissions
from .models import Tarefa
from .serializers import TarefaSerializer

class TarefaListCreate(generics.ListCreateAPIView):
    serializer_class = TarefaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Tarefa.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TarefaDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TarefaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Tarefa.objects.filter(user=self.request.user)
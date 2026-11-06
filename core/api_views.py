from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import generics
from rest_framework.exceptions import ValidationError as DRFValidationError

from .models import Tarefa
from .serializers import TarefaSerializer


class TratarErrosMixin:
    """Converte ValidationError do model (chamado em Tarefa.save) em resposta 400."""

    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user)
        except DjangoValidationError as e:
            raise DRFValidationError({'detail': e.messages})

    def perform_update(self, serializer):
        try:
            serializer.save()
        except DjangoValidationError as e:
            raise DRFValidationError({'detail': e.messages})


class TarefaListCreate(TratarErrosMixin, generics.ListCreateAPIView):
    serializer_class = TarefaSerializer

    def get_queryset(self):
        return Tarefa.objects.filter(user=self.request.user).order_by('-criada_em')


class TarefaDetail(TratarErrosMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TarefaSerializer

    def get_queryset(self):
        return Tarefa.objects.filter(user=self.request.user)

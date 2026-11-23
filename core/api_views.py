from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import generics
from rest_framework.exceptions import ValidationError as DRFValidationError
from .tenancy import org_atual


from .models import Tarefa, Projeto, Subtarefa, Dependencia, Membro
from .serializers import (
    TarefaSerializer, ProjetoSerializer,
    SubtarefaSerializer, DependenciaSerializer,
)


def _erro_drf(e):
    if hasattr(e, 'error_dict'):
        return DRFValidationError(e.message_dict)
    return DRFValidationError({'detail': e.messages})


class TratarErrosMixin:
   
    def extras_criacao(self):
        return {}

    def perform_create(self, serializer):
        try:
            serializer.save(**self.extras_criacao())
        except DjangoValidationError as e:
            raise _erro_drf(e)

    def perform_update(self, serializer):
        try:
            serializer.save()
        except DjangoValidationError as e:
            raise _erro_drf(e)


# ---- Tarefas ----
class TarefaListCreate(TratarErrosMixin, generics.ListCreateAPIView):
    serializer_class = TarefaSerializer

    def get_queryset(self):
        return Tarefa.objects.filter(user=self.request.user).order_by('-criada_em')

    def extras_criacao(self):
        return {'user': self.request.user, 'organizacao': org_atual(self.request)}


class TarefaDetail(TratarErrosMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TarefaSerializer

    def get_queryset(self):
        return Tarefa.objects.filter(user=self.request.user)


# ---- Projetos ----
class ProjetoListCreate(TratarErrosMixin, generics.ListCreateAPIView):
    serializer_class = ProjetoSerializer

    def get_queryset(self):
        return Projeto.objects.filter(dono__user=self.request.user).order_by('-criado_em')

    def extras_criacao(self):
        org = org_atual(self.request)
        return {'dono': self.request.user.membro, 'organizacao': org}


class ProjetoDetail(TratarErrosMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProjetoSerializer

    def get_queryset(self):
        return Projeto.objects.filter(dono__user=self.request.user)


# ---- Subtarefas ----
class SubtarefaListCreate(TratarErrosMixin, generics.ListCreateAPIView):
    serializer_class = SubtarefaSerializer

    def get_queryset(self):
        return Subtarefa.objects.filter(tarefa__user=self.request.user).order_by('-criada_em')

    def extras_criacao(self):
        return {'organizacao': org_atual(self.request)}



class SubtarefaDetail(TratarErrosMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SubtarefaSerializer

    def get_queryset(self):
        return Subtarefa.objects.filter(tarefa__user=self.request.user)

class DependenciaListCreate(TratarErrosMixin, generics.ListCreateAPIView):
    serializer_class = DependenciaSerializer

    def get_queryset(self):
        return Dependencia.objects.filter(tarefa__user=self.request.user)

    def extras_criacao(self):
        return {'organizacao': org_atual(self.request)}


class DependenciaDetail(generics.RetrieveDestroyAPIView):
    serializer_class = DependenciaSerializer

    def get_queryset(self):
        return Dependencia.objects.filter(tarefa__user=self.request.user)
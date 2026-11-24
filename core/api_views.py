from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import generics
from rest_framework.exceptions import ValidationError as DRFValidationError

from .models import Tarefa, Projeto, Subtarefa, Dependencia
from .serializers import (
    TarefaSerializer, ProjetoSerializer,
    SubtarefaSerializer, DependenciaSerializer,
)
from .tenancy import org_atual
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .dashboard import base_queryset, metricas
from .forms import PeriodoForm, filtrar_periodo


def _erro_drf(e):
    if hasattr(e, 'error_dict'):
        return DRFValidationError(e.message_dict)
    return DRFValidationError({'detail': e.messages})


class TratarErrosMixin:
    """Converte ValidationError do model (lançado no save) em resposta 400."""

    def extras_criacao(self):
        return {'organizacao': org_atual(self.request)}

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
        return Tarefa.objects.filter(organizacao=org_atual(self.request)).order_by('-criada_em')

    def extras_criacao(self):
        return {**super().extras_criacao(), 'user': self.request.user}


class TarefaDetail(TratarErrosMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TarefaSerializer

    def get_queryset(self):
        return Tarefa.objects.filter(organizacao=org_atual(self.request))


# ---- Projetos ----
class ProjetoListCreate(TratarErrosMixin, generics.ListCreateAPIView):
    serializer_class = ProjetoSerializer

    def get_queryset(self):
        return Projeto.objects.filter(organizacao=org_atual(self.request)).order_by('-criado_em')

    def extras_criacao(self):
        return {**super().extras_criacao(), 'dono': self.request.user.perfil}


class ProjetoDetail(TratarErrosMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProjetoSerializer

    def get_queryset(self):
        return Projeto.objects.filter(organizacao=org_atual(self.request))


# ---- Subtarefas ----
class SubtarefaListCreate(TratarErrosMixin, generics.ListCreateAPIView):
    serializer_class = SubtarefaSerializer

    def get_queryset(self):
        return Subtarefa.objects.filter(organizacao=org_atual(self.request)).order_by('-criada_em')


class SubtarefaDetail(TratarErrosMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SubtarefaSerializer

    def get_queryset(self):
        return Subtarefa.objects.filter(organizacao=org_atual(self.request))


# ---- Dependências (sem edição: apaga e cria de novo) ----
class DependenciaListCreate(TratarErrosMixin, generics.ListCreateAPIView):
    serializer_class = DependenciaSerializer

    def get_queryset(self):
        return Dependencia.objects.filter(organizacao=org_atual(self.request))


class DependenciaDetail(generics.RetrieveDestroyAPIView):
    serializer_class = DependenciaSerializer

    def get_queryset(self):
        return Dependencia.objects.filter(organizacao=org_atual(self.request))

class DashboardApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = org_atual(request)
        form = PeriodoForm(request.GET)
        if not form.is_valid():
            return Response(form.errors, status=400)
        base = filtrar_periodo(form, base_queryset(org))
        # Mesma regra da tela: série mensal só para administrador.
        return Response(metricas(base, incluir_series=request.user.perfil.eh_admin))
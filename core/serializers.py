from rest_framework import serializers
from .models import Tarefa, Projeto, Subtarefa, Dependencia
import copy
from django.core.exceptions import ValidationError as DjangoValidationError
from .tenancy import org_atual

def _tarefas_do_usuario(serializer):
    request = serializer.context.get('request')
    if request and request.user.is_authenticated:
        return Tarefa.objects.filter(user=request.user)
    return Tarefa.objects.none()


class ProjetoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Projeto
        fields = ['id', 'nome', 'descricao', 'criado_em']
        read_only_fields = ['criado_em']

def _tem_ciclo(tarefa, depende_de):
    """True se criar 'tarefa depende de depende_de' fecharia um ciclo."""
    if tarefa.pk == depende_de.pk:
        return True
    visitados = set()
    pilha = [depende_de]
    while pilha:
        atual = pilha.pop()
        if atual.pk == tarefa.pk:
            return True
        if atual.pk in visitados:
            continue
        visitados.add(atual.pk)
        pilha.extend(d.depende_de for d in atual.dependencias.select_related('depende_de'))
    return False

class TarefaSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tarefa
        fields = ['id', 'titulo', 'concluida', 'prazo', 'projeto']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            self.fields['projeto'].queryset = Projeto.objects.filter(
                dono__user=request.user
            )

    def validate_titulo(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                'O título deve ter pelo menos 3 caracteres.'
            )
        return value

    def validate(self, data):
        request = self.context['request']

        # Monta a tarefa com os novos valores para reaproveitar o clean() do modelo
        tarefa = copy.copy(self.instance) if self.instance else Tarefa(user=request.user)
        for attr, valor in data.items():
            setattr(tarefa, attr, valor)
        tarefa.organizacao = org_atual(request)
        try:
            tarefa.clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)

        if data.get('concluida') and self.instance and not self.instance.pode_ser_concluida():
            raise serializers.ValidationError(
                {'concluida': 'Há dependências pendentes.'}
            )
        return data


class SubtarefaSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subtarefa
        fields = ['id', 'tarefa', 'titulo', 'concluida']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tarefa'].queryset = _tarefas_do_usuario(self)

class DependenciaSerializer(serializers.ModelSerializer):

    class Meta:
        model = Dependencia
        fields = ['id', 'tarefa', 'depende_de']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = _tarefas_do_usuario(self)
        self.fields['tarefa'].queryset = qs
        self.fields['depende_de'].queryset = qs

    def validate(self, data):
        if _tem_ciclo(data['tarefa'], data['depende_de']):
            raise serializers.ValidationError(
                'Essa dependência criaria um ciclo entre tarefas.'
            )
        return data
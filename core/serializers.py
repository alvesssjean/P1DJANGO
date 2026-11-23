from rest_framework import serializers
from .models import Tarefa, Projeto, Subtarefa, Dependencia
from .tenancy import org_do_usuario


def _org(serializer):
    request = serializer.context.get('request')
    return org_do_usuario(request.user) if request else None


def _tarefas_da_org(serializer):
    org = _org(serializer)
    return Tarefa.objects.filter(organizacao=org) if org else Tarefa.objects.none()


class ProjetoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Projeto
        fields = ['id', 'nome', 'descricao', 'criado_em']
        read_only_fields = ['criado_em']


class TarefaSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tarefa
        fields = ['id', 'titulo', 'concluida', 'prazo', 'projeto']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        org = _org(self)
        self.fields['projeto'].queryset = (
            Projeto.objects.filter(organizacao=org) if org else Projeto.objects.none()
        )

    def validate_titulo(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                'O título deve ter pelo menos 3 caracteres.'
            )
        return value

    # Prazo, projeto da mesma organização e bloqueio por dependência
    # ficam em Tarefa.clean(): a API herda via full_clean() no save().


class SubtarefaSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subtarefa
        fields = ['id', 'tarefa', 'titulo', 'concluida']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tarefa'].queryset = _tarefas_da_org(self)


class DependenciaSerializer(serializers.ModelSerializer):

    class Meta:
        model = Dependencia
        fields = ['id', 'tarefa', 'depende_de']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tarefas = _tarefas_da_org(self)
        self.fields['tarefa'].queryset = tarefas
        self.fields['depende_de'].queryset = tarefas

    # Auto-dependência, ciclo e mesma organização: Dependencia.clean().
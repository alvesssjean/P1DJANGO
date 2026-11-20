from rest_framework import serializers
from .models import Tarefa, Projeto, Subtarefa, Dependencia


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
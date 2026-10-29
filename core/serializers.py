from .models import Tarefa
from rest_framework import serializers

class TarefaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tarefa
        fields = ['id', 'título', 'concluida', 'prazo', 'criada_em', 'projeto']
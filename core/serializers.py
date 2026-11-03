from .models import Tarefa
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError

class TarefaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tarefa
        fields = ['id', 'titulo', 'concluida', 'prazo', 'criada_em', 'projeto']
        read_only_fields = ['id', 'criada_em']

    def validate(self, data):
        instancia = self.instance or Tarefa(user=self.context['request'].user)
        for campo, valor in data.items():
            setattr(instancia, campo, valor)
        try:
            instancia.clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return data
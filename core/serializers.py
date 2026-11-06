from rest_framework import serializers
from .models import Tarefa, Projeto


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
        projeto = data.get('projeto')
        prazo = data.get('prazo')

        # Mesma regra de forms.py (clean_prazo)
        if projeto and prazo and prazo < projeto.criado_em.date():
            raise serializers.ValidationError({
                'prazo': 'O prazo não pode ser anterior à criação do projeto.'
            })

        # Mesma regra de Tarefa.clean(), mas em JSON
        if data.get('concluida') and self.instance and not self.instance.pode_ser_concluida():
            raise serializers.ValidationError({
                'concluida': 'Existem dependências ainda não concluídas.'
            })

        return data

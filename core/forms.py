from django import forms
from .models import Tarefa, Projeto

class TarefaForm(forms.ModelForm):

    class Meta:
        model = Tarefa
        fields = ['titulo', 'projeto']

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['projeto'].required = False
        if user is not None:
            self.fields['projeto'].queryset = Projeto.objects.filter(dono__user=user)
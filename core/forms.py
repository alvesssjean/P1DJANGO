from django import forms
from .models import Tarefa, Projeto, Dependencia


class ProjetoForm(forms.ModelForm):

    class Meta:
        model = Projeto
        fields = ['nome', 'descricao']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
        }


class TarefaForm(forms.ModelForm):

    class Meta:
        model = Tarefa
        fields = ['titulo', 'projeto', 'prazo']
        widgets = {
            'prazo': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['projeto'].required = False
        self.fields['prazo'].required = False
        if user is not None:
            self.fields['projeto'].queryset = Projeto.objects.filter(dono__user=user)


class DependenciaForm(forms.ModelForm):

    class Meta:
        model = Dependencia
        fields = ['tarefa', 'depende_de']
        labels = {
            'tarefa': 'Tarefa',
            'depende_de': 'Depende de',
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            tarefas_do_usuario = Tarefa.objects.filter(user=user)
            self.fields['tarefa'].queryset = tarefas_do_usuario
            self.fields['depende_de'].queryset = tarefas_do_usuario
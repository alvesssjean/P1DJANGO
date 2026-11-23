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

    def __init__(self, *args, org=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['projeto'].required = False
        self.fields['prazo'].required = False
        self.fields['projeto'].queryset = (
            Projeto.objects.filter(organizacao=org) if org else Projeto.objects.none()
        )


class DependenciaForm(forms.ModelForm):

    class Meta:
        model = Dependencia
        fields = ['tarefa', 'depende_de']
        labels = {
            'tarefa': 'Tarefa',
            'depende_de': 'Depende de',
        }

    def __init__(self, *args, org=None, **kwargs):
        super().__init__(*args, **kwargs)
        tarefas = Tarefa.objects.filter(organizacao=org) if org else Tarefa.objects.none()
        self.fields['tarefa'].queryset = tarefas
        self.fields['depende_de'].queryset = tarefas
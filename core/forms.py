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

    def clean_prazo(self):
        prazo = self.cleaned_data.get('prazo')
        projeto = self.cleaned_data.get('projeto')

        if prazo and projeto:
            data_criacao_projeto = projeto.criado_em.date()
            if prazo < data_criacao_projeto:
                raise forms.ValidationError(
                    'O prazo da tarefa não pode ser anterior à data de criação '
                    f'do projeto "{projeto.nome}" ({data_criacao_projeto.strftime("%d/%m/%Y")}).'
                )

        return prazo


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

    def clean(self):
        cleaned_data = super().clean()
        tarefa = cleaned_data.get('tarefa')
        depende_de = cleaned_data.get('depende_de')

        if tarefa and depende_de:
            if tarefa == depende_de:
                raise forms.ValidationError('Uma tarefa não pode depender dela mesma.')

            if Dependencia.objects.filter(tarefa=tarefa, depende_de=depende_de).exists():
                raise forms.ValidationError('Essa dependência já foi cadastrada.')

            # Percorre a cadeia de dependências partindo de "depende_de":
            # se em algum ponto chegarmos de volta em "tarefa", criar esse
            # vínculo fecharia um ciclo.
            visitados = set()
            pilha = [depende_de]
            while pilha:
                atual = pilha.pop()
                if atual == tarefa:
                    raise forms.ValidationError(
                        f'Essa dependência criaria um ciclo: "{depende_de}" já depende '
                        f'(direta ou indiretamente) de "{tarefa}".'
                    )
                if atual.pk in visitados:
                    continue
                visitados.add(atual.pk)
                proximos_ids = Dependencia.objects.filter(tarefa=atual).values_list('depende_de_id', flat=True)
                pilha.extend(Tarefa.objects.filter(pk__in=proximos_ids))

        return cleaned_data
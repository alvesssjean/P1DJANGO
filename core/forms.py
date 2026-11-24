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

class PeriodoForm(forms.Form):
    inicio = forms.DateField(
        required=False, label='Início', widget=forms.DateInput(attrs={'type': 'date'}))
    fim = forms.DateField(
        required=False, label='Fim', widget=forms.DateInput(attrs={'type': 'date'}))

    def clean(self):
        dados = super().clean()
        inicio, fim = dados.get('inicio'), dados.get('fim')
        if inicio and fim and inicio > fim:
            raise forms.ValidationError('A data inicial não pode ser posterior à final.')
        return dados


def filtrar_periodo(form, qs):
    """Aplica o período só se o form for válido (nunca confie na data da URL)."""
    if form.is_valid():
        inicio = form.cleaned_data.get('inicio')
        fim = form.cleaned_data.get('fim')
        if inicio:
            qs = qs.filter(criada_em__date__gte=inicio)
        if fim:
            qs = qs.filter(criada_em__date__lte=fim)
    return qs
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Tarefa, Membro, Projeto
from django.contrib import messages
from django.core.exceptions import ValidationError
from .forms import TarefaForm, ProjetoForm, DependenciaForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    tipo_formulario = request.POST.get('form_type')

    if request.method == 'POST' and tipo_formulario == 'projeto':
        projeto_form = ProjetoForm(request.POST)
        tarefa_form = TarefaForm(user=request.user)
        dependencia_form = DependenciaForm(user=request.user)
        if projeto_form.is_valid():
            projeto = projeto_form.save(commit=False)
            membro, _ = Membro.objects.get_or_create(user=request.user)
            projeto.dono = membro
            projeto.save()
            return redirect('home')

    elif request.method == 'POST' and tipo_formulario == 'tarefa':
        tarefa_form = TarefaForm(request.POST, user=request.user)
        projeto_form = ProjetoForm()
        dependencia_form = DependenciaForm(user=request.user)
        if tarefa_form.is_valid():
            tarefa = tarefa_form.save(commit=False)
            tarefa.user = request.user
            tarefa.save()
            return redirect('home')

    elif request.method == 'POST' and tipo_formulario == 'dependencia':
        dependencia_form = DependenciaForm(request.POST, user=request.user)
        tarefa_form = TarefaForm(user=request.user)
        projeto_form = ProjetoForm()
        if dependencia_form.is_valid():
            dependencia_form.save()
            return redirect('home')

    else:
        tarefa_form = TarefaForm(user=request.user)
        projeto_form = ProjetoForm()
        dependencia_form = DependenciaForm(user=request.user)

    tarefas_query = Tarefa.objects.filter(user=request.user)

    # Feature 1 - Busca e Filtro na Listagem
    termo_busca = request.GET.get('q', '')
    status_filtro = request.GET.get('status', '')

    if termo_busca:
        tarefas_query = tarefas_query.filter(titulo__icontains=termo_busca)

    if status_filtro == 'pendentes':
        tarefas_query = tarefas_query.filter(concluida=False)
    elif status_filtro == 'concluidas':
        tarefas_query = tarefas_query.filter(concluida=True)

    todas_as_tarefas = tarefas_query.order_by('-criada_em')
    projetos_do_usuario = Projeto.objects.filter(dono__user=request.user).order_by('-criado_em')

    context = {
        'nome_usuario': request.user.username,
        'tecnologias': ['Autenticação', 'ForeignKey', 'Login'],
        'tarefas': todas_as_tarefas,
        'tarefa_form': tarefa_form,
        'projeto_form': projeto_form,
        'dependencia_form': dependencia_form,
        'projetos': projetos_do_usuario,
        'termo_busca': termo_busca,
        'status_filtro': status_filtro,
    }
    return render(request, 'home.html', context)

@login_required
def concluir_tarefa(request, pk):
    tarefa = get_object_or_404(Tarefa, pk=pk, user=request.user)

    if request.method == 'POST':
        tarefa.concluida = True
        try:
            tarefa.save()
        except ValidationError as e:
            messages.error(request, ' '.join(e.messages))
        return redirect('home')

@login_required 
def deletar_tarefa(request, pk):
    tarefa = get_object_or_404(Tarefa, pk=pk, user=request.user)

    if request.method == 'POST':
        tarefa.delete()
        return redirect('home')
    
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Membro.objects.create(user=user)
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    context = {'form': form}
    return render(request, 'register.html', context)
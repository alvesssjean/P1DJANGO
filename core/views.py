from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .forms import TarefaForm, ProjetoForm, DependenciaForm, PeriodoForm, filtrar_periodo
from .models import Tarefa, Projeto, Organizacao, Perfil
from .tenancy import org_atual
import csv
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils import timezone
from .dashboard import base_queryset, metricas, situacao
from .permissoes import papel_requerido


@login_required
def home(request):
    org = org_atual(request)
    tipo_formulario = request.POST.get('form_type')

    projeto_form = ProjetoForm()
    tarefa_form = TarefaForm(org=org)
    dependencia_form = DependenciaForm(org=org)

    if request.method == 'POST' and tipo_formulario == 'projeto':
        projeto_form = ProjetoForm(request.POST)
        if projeto_form.is_valid():
            projeto = projeto_form.save(commit=False)
            projeto.organizacao = org               # vem do usuário, nunca do form
            projeto.dono = request.user.perfil
            projeto.save()
            return redirect('home')

    elif request.method == 'POST' and tipo_formulario == 'tarefa':
        tarefa_form = TarefaForm(request.POST, org=org)
        if tarefa_form.is_valid():
            tarefa = tarefa_form.save(commit=False)
            tarefa.organizacao = org
            tarefa.user = request.user
            tarefa.save()
            return redirect('home')

    elif request.method == 'POST' and tipo_formulario == 'dependencia':
        dependencia_form = DependenciaForm(request.POST, org=org)
        if dependencia_form.is_valid():
            dependencia = dependencia_form.save(commit=False)
            dependencia.organizacao = org
            dependencia.save()
            return redirect('home')

    tarefas_query = Tarefa.objects.filter(organizacao=org)

    # Busca e filtro na listagem
    termo_busca = request.GET.get('q', '')
    status_filtro = request.GET.get('status', '')

    if termo_busca:
        tarefas_query = tarefas_query.filter(titulo__icontains=termo_busca)

    if status_filtro == 'pendentes':
        tarefas_query = tarefas_query.filter(concluida=False)
    elif status_filtro == 'concluidas':
        tarefas_query = tarefas_query.filter(concluida=True)

    context = {
        'nome_usuario': request.user.username,
        'organizacao': org,
        'tarefas': tarefas_query.order_by('-criada_em'),
        'tarefa_form': tarefa_form,
        'projeto_form': projeto_form,
        'dependencia_form': dependencia_form,
        'projetos': Projeto.objects.filter(organizacao=org).order_by('-criado_em'),
        'termo_busca': termo_busca,
        'status_filtro': status_filtro,
    }
    return render(request, 'home.html', context)


@login_required
@require_POST
def concluir_tarefa(request, pk):
    tarefa = get_object_or_404(Tarefa, pk=pk, organizacao=org_atual(request))
    tarefa.concluida = True
    try:
        tarefa.save()
    except ValidationError as e:
        messages.error(request, ' '.join(e.messages))
    return redirect('home')


@login_required
@require_POST
def deletar_tarefa(request, pk):
    tarefa = get_object_or_404(Tarefa, pk=pk, organizacao=org_atual(request))
    tarefa.delete()
    return redirect('home')


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                org = Organizacao.objects.create(nome=f'Organização de {user.username}')
                Perfil.objects.create(usuario=user, organizacao=org, papel=Perfil.ADMIN)
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

@login_required
def dashboard(request):
    org = org_atual(request)
    eh_admin = request.user.perfil.eh_admin
    form = PeriodoForm(request.GET)
    base = filtrar_periodo(form, base_queryset(org))
    contexto = {
        'organizacao': org,
        'form': form,
        'mostra_series': eh_admin,   # operador vê versão parcial
        'pode_exportar': eh_admin,
        **metricas(base, incluir_series=eh_admin),
    }
    return render(request, 'dashboard.html', contexto)

def _celula_segura(valor):
    """Evita injeção de fórmula: o Excel interpreta =, +, -, @ no início."""
    texto = '' if valor is None else str(valor)
    if texto.startswith(('=', '+', '-', '@', '\t', '\r')):
        return "'" + texto
    return texto


@papel_requerido('admin')
def exportar_csv(request):
    org = org_atual(request)
    form = PeriodoForm(request.GET)
    if not form.is_valid():
        return HttpResponseBadRequest('Período inválido.')
    hoje = timezone.localdate()
    qs = (
        filtrar_periodo(form, base_queryset(org))
        .select_related('projeto', 'user')
        .order_by('-criada_em')
    )
    resp = HttpResponse(content_type='text/csv; charset=utf-8')
    resp['Content-Disposition'] = 'attachment; filename="tarefas.csv"'
    resp.write('\ufeff')  # BOM: o Excel abre os acentos corretamente
    w = csv.writer(resp, delimiter=';')  # ';' é o separador do Excel em pt-BR
    w.writerow(['Título', 'Projeto', 'Criada por', 'Criada em', 'Prazo', 'Situação'])
    for t in qs:
        w.writerow([
            _celula_segura(t.titulo),
            _celula_segura(t.projeto.nome if t.projeto else ''),
            _celula_segura(t.user.username),
            timezone.localtime(t.criada_em).strftime('%d/%m/%Y %H:%M'),
            t.prazo.strftime('%d/%m/%Y') if t.prazo else '',
            situacao(t, hoje),
        ])
    return resp
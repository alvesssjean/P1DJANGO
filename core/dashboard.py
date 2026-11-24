from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone

from .models import Tarefa


def base_queryset(org):
    """Primeira linha de toda métrica: só dados da organização."""
    return Tarefa.objects.filter(organizacao=org)


def calcular_kpis(base, hoje=None):
    """Cartões: vários totais em uma única consulta."""
    hoje = hoje or timezone.localdate()
    return base.aggregate(
        total=Count('id'),
        concluidas=Count('id', filter=Q(concluida=True)),
        pendentes=Count('id', filter=Q(concluida=False)),
        atrasadas=Count('id', filter=Q(concluida=False, prazo__lt=hoje)),
        responsaveis=Count('user', distinct=True),
    )


def ranking_projetos(base, limite=5):
    return list(
        base.filter(projeto__isnull=False)
        .values('projeto_id', 'projeto__nome')
        .annotate(total=Count('id'), pendentes=Count('id', filter=Q(concluida=False)))
        .order_by('-total', 'projeto__nome')[:limite]
    )


def tarefas_por_mes(base):
    qs = (
        base.annotate(mes=TruncMonth('criada_em'))
        .values('mes')
        .annotate(total=Count('id'))
        .order_by('mes')
    )
    return [{'mes': r['mes'].strftime('%m/%Y'), 'total': r['total']} for r in qs]


def distribuicao_status(kpis):
    """Sem consulta extra: deriva dos KPIs já calculados."""
    return [
        {'status': 'Concluídas', 'total': kpis['concluidas']},
        {'status': 'Pendentes no prazo', 'total': kpis['pendentes'] - kpis['atrasadas']},
        {'status': 'Atrasadas', 'total': kpis['atrasadas']},
    ]


def situacao(tarefa, hoje):
    if tarefa.concluida:
        return 'Concluída'
    if tarefa.prazo and tarefa.prazo < hoje:
        return 'Atrasada'
    return 'Pendente'


def metricas(base, incluir_series=False):
    """Único lugar que monta as métricas (usado pela tela e pela API)."""
    kpis = calcular_kpis(base)
    dados = {
        'kpis': kpis,
        'ranking': ranking_projetos(base),
        'distribuicao': distribuicao_status(kpis),
    }
    if incluir_series:
        dados['por_mes'] = tarefas_por_mes(base)
    return dados
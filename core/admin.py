from django.contrib import admin
from .models import Organizacao, Projeto, Tarefa, Subtarefa, Dependencia


@admin.register(Organizacao)
class OrganizacaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'criada_em')
    search_fields = ('nome',)


@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'organizacao', 'dono')
    list_filter = ('organizacao',)


@admin.register(Tarefa)
class TarefaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'organizacao', 'projeto', 'concluida', 'prazo')
    list_filter = ('organizacao', 'concluida')


@admin.register(Subtarefa)
class SubtarefaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'organizacao', 'tarefa', 'concluida')
    list_filter = ('organizacao',)


@admin.register(Dependencia)
class DependenciaAdmin(admin.ModelAdmin):
    list_display = ('tarefa', 'depende_de', 'organizacao')
    list_filter = ('organizacao',)
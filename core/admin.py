from django.contrib import admin
from .models import Membro, Projeto, Tarefa, Subtarefa, Dependencia

admin.site.register(Membro)
admin.site.register(Projeto)
admin.site.register(Tarefa)
admin.site.register(Subtarefa)
admin.site.register(Dependencia)
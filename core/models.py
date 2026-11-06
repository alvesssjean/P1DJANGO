from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Membro(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='membro')

    def __str__(self):
        return self.user.username


class Projeto(models.Model):
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    dono = models.ForeignKey(Membro, on_delete=models.CASCADE, related_name='projetos_criados')
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome


class Tarefa(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    projeto = models.ForeignKey(
        Projeto, on_delete=models.CASCADE, related_name='tarefas',
        null=True, blank=True
    )
    titulo = models.CharField(max_length=200)
    concluida = models.BooleanField(default=False)
    prazo = models.DateField(null=True, blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

    def dependencias_pendentes(self):
        return self.dependencias.filter(depende_de__concluida=False)

    def pode_ser_concluida(self):
        return not self.dependencias_pendentes().exists()

    def clean(self):
        if self.concluida and self.pk and not self.pode_ser_concluida():
            raise ValidationError(
                'Não é possível concluir esta tarefa: existem dependências ainda não concluídas.'
            )


    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Subtarefa(models.Model):
    tarefa = models.ForeignKey(Tarefa, on_delete=models.CASCADE, related_name='subtarefas')
    titulo = models.CharField(max_length=200)
    concluida = models.BooleanField(default=False)
    criada_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo


class Dependencia(models.Model):
    tarefa = models.ForeignKey(Tarefa, on_delete=models.CASCADE, related_name='dependencias')
    depende_de = models.ForeignKey(Tarefa, on_delete=models.CASCADE, related_name='bloqueia')

    class Meta:
        unique_together = ('tarefa', 'depende_de')

    def __str__(self):
        return f'{self.tarefa} depende de {self.depende_de}'

    def _criaria_ciclo(self):
        visitados = set()
        pilha = [self.depende_de]
        while pilha:
            atual = pilha.pop()
            if atual.pk == self.tarefa_id:
                return True
            if atual.pk in visitados:
                continue
            visitados.add(atual.pk)
            ids = Dependencia.objects.filter(tarefa=atual).values_list('depende_de_id', flat=True)
            pilha.extend(Tarefa.objects.filter(pk__in=ids))
        return False

    def clean(self):
        if self.tarefa_id is None or self.depende_de_id is None:
            return
        if self.tarefa_id == self.depende_de_id:
            raise ValidationError('Uma tarefa não pode depender dela mesma.')
        if self._criaria_ciclo():
            raise ValidationError('Essa dependência criaria um ciclo.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

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
    criada_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

    def dependencias_pendentes(self):
        return self.dependencias.filter(depende_de__concluida=False)

    def pode_ser_concluida(self):
        return not self.dependencias_pendentes().exists()

    def clean(self):
        if self.concluida and not self.pode_ser_concluida():
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

    def clean(self):
        if self.tarefa_id == self.depende_de_id:
            raise ValidationError('Uma tarefa não pode depender dela mesma.')

    def __str__(self):
        return f'{self.tarefa} depende de {self.depende_de}'
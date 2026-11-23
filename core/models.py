from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


class Organizacao(models.Model):
    nome = models.CharField(max_length=120)
    criada_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome


class DaOrganizacao(models.Model):
    # TEMPORÁRIO (passo 1 da migração). Será removido no Bloco 3.
    organizacao = models.ForeignKey(
        Organizacao, on_delete=models.PROTECT, null=True)

    class Meta:
        abstract = True


class Perfil(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    organizacao = models.ForeignKey(Organizacao, on_delete=models.PROTECT)

    def __str__(self):
        return f'{self.usuario.username} ({self.organizacao})'


class Membro(DaOrganizacao):
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='membro')

    def __str__(self):
        return self.user.username


class Projeto(DaOrganizacao):
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    dono = models.ForeignKey(Membro, on_delete=models.CASCADE,
                             related_name='projetos_criados')
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome


class Tarefa(DaOrganizacao):
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
        if self.projeto_id and self.organizacao_id:
            if self.projeto.organizacao_id != self.organizacao_id:
                raise ValidationError({
                    'projeto': 'O projeto pertence a outra organização.'
                })
        if self.prazo and self.projeto_id:
            criacao = timezone.localtime(self.projeto.criado_em).date()
            if self.prazo < criacao:
                raise ValidationError({
                    'prazo': (
                        f'O prazo não pode ser anterior à criação do projeto '
                        f'"{self.projeto.nome}" ({criacao:%d/%m/%Y}).'
                    )
                })


class Subtarefa(DaOrganizacao):
    tarefa = models.ForeignKey(Tarefa, on_delete=models.CASCADE, related_name='subtarefas')
    titulo = models.CharField(max_length=200)
    concluida = models.BooleanField(default=False)
    criada_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

    def clean(self):
        if self.tarefa_id and self.organizacao_id \
                and self.tarefa.organizacao_id != self.organizacao_id:
            raise ValidationError('A subtarefa deve ser da mesma organização da tarefa.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Dependencia(DaOrganizacao):
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

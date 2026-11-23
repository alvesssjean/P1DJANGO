from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


class Organizacao(models.Model):
    """O 'inquilino': dono de todos os dados de negócio."""
    nome = models.CharField(max_length=120)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'organização'
        verbose_name_plural = 'organizações'

    def __str__(self):
        return self.nome


class Perfil(models.Model):
    """Liga o usuário à sua organização (o papel entra na Aula 15)."""
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    organizacao = models.ForeignKey(Organizacao, on_delete=models.PROTECT)

    def __str__(self):
        return f'{self.usuario.username} ({self.organizacao})'


class DaOrganizacao(models.Model):
    """Base abstrata: todo model de negócio herda daqui."""
    organizacao = models.ForeignKey(Organizacao, on_delete=models.PROTECT)

    class Meta:
        abstract = True


class Projeto(DaOrganizacao):
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    # "dono" = quem criou. A posse dos dados é da organização.
    dono = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name='projetos_criados')
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
        if self.projeto_id and self.organizacao_id \
                and self.projeto.organizacao_id != self.organizacao_id:
            raise ValidationError({'projeto': 'Esse projeto pertence a outra organização.'})
        if self.prazo and self.projeto_id:
            criacao = timezone.localtime(self.projeto.criado_em).date()
            if self.prazo < criacao:
                raise ValidationError({
                    'prazo': (
                        f'O prazo não pode ser anterior à criação do projeto '
                        f'"{self.projeto.nome}" ({criacao:%d/%m/%Y}).'
                    )
                })
        if self.concluida and self.pk and not self.pode_ser_concluida():
            raise ValidationError(
                'Não é possível concluir esta tarefa: existem dependências ainda não concluídas.'
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


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
        return False

    def clean(self):
        if self.tarefa_id is None or self.depende_de_id is None:
            return
        if self.tarefa_id == self.depende_de_id:
            raise ValidationError('Uma tarefa não pode depender dela mesma.')
        if self.tarefa.organizacao_id != self.depende_de.organizacao_id:
            raise ValidationError('As duas tarefas precisam ser da mesma organização.')
        if self.organizacao_id and self.organizacao_id != self.tarefa.organizacao_id:
            raise ValidationError('A dependência deve ser da mesma organização das tarefas.')
        if self._criaria_ciclo():
            raise ValidationError('Essa dependência criaria um ciclo.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
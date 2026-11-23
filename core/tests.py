from datetime import timedelta

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from .models import Membro, Organizacao, Projeto, Tarefa, Dependencia


class ApiTests(APITestCase):

    def setUp(self):
        self.org = Organizacao.objects.create(nome='Org Teste')
        self.ana = User.objects.create_user('ana', password='senha12345')
        self.beto = User.objects.create_user('beto', password='senha12345')
        Membro.objects.create(user=self.ana, organizacao=self.org)
        Membro.objects.create(user=self.beto, organizacao=self.org)
        self.t_ana = Tarefa.objects.create(
            user=self.ana, organizacao=self.org, titulo='Tarefa da Ana')
        self.t_beto = Tarefa.objects.create(
            user=self.beto, organizacao=self.org, titulo='Tarefa do Beto')

    def test_sem_login_nao_acessa(self):
        r = self.client.get(reverse('api_tarefas'))
        self.assertIn(r.status_code, (401, 403))

    def test_lista_so_as_tarefas_do_proprio_usuario(self):
        self.client.force_authenticate(self.ana)
        r = self.client.get(reverse('api_tarefas'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual([t['titulo'] for t in r.json()], ['Tarefa da Ana'])

    def test_detalhe_de_outro_usuario_da_404(self):
        self.client.force_authenticate(self.ana)
        r = self.client.get(reverse('api_tarefa_detalhe', args=[self.t_beto.pk]))
        self.assertEqual(r.status_code, 404)

    def test_criar_tarefa_retorna_201(self):
        self.client.force_authenticate(self.ana)
        r = self.client.post(reverse('api_tarefas'), {'titulo': 'Nova tarefa'}, format='json')
        self.assertEqual(r.status_code, 201)
        self.assertTrue(Tarefa.objects.filter(user=self.ana, titulo='Nova tarefa').exists())

    def test_titulo_curto_retorna_400(self):
        self.client.force_authenticate(self.ana)
        r = self.client.post(reverse('api_tarefas'), {'titulo': 'ab'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_prazo_anterior_ao_projeto_retorna_400(self):
        membro = Membro.objects.get(user=self.ana)
        projeto = Projeto.objects.create(nome='P', dono=membro, organizacao=self.org)
        ontem = timezone.localdate() - timedelta(days=1)
        self.client.force_authenticate(self.ana)
        r = self.client.post(reverse('api_tarefas'), {
            'titulo': 'Com prazo', 'projeto': projeto.pk, 'prazo': ontem.isoformat(),
        }, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertIn('prazo', r.json())

    def test_nao_conclui_com_dependencia_pendente(self):
        outra = Tarefa.objects.create(
            user=self.ana, organizacao=self.org, titulo='Outra tarefa')
        Dependencia.objects.create(
            tarefa=outra, depende_de=self.t_ana, organizacao=self.org)
        self.client.force_authenticate(self.ana)
        r = self.client.patch(
            reverse('api_tarefa_detalhe', args=[outra.pk]), {'concluida': True}, format='json'
        )
        self.assertEqual(r.status_code, 400)

    def test_ciclo_de_dependencia_retorna_400(self):
        outra = Tarefa.objects.create(
            user=self.ana, organizacao=self.org, titulo='Outra tarefa')
        Dependencia.objects.create(
            tarefa=outra, depende_de=self.t_ana, organizacao=self.org)
        self.client.force_authenticate(self.ana)
        r = self.client.post(reverse('api_dependencias'), {
            'tarefa': self.t_ana.pk, 'depende_de': outra.pk,
        }, format='json')
        self.assertEqual(r.status_code, 400)

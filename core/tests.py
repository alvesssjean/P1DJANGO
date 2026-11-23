from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from .models import Organizacao, Perfil, Projeto, Tarefa, Subtarefa, Dependencia


def criar_usuario(nome, org):
    usuario = User.objects.create_user(nome, password='senha12345')
    Perfil.objects.create(usuario=usuario, organizacao=org)
    return usuario


class DadosBase:
    """Duas organizações: A (ana e carla) e B (beto)."""

    def setUp(self):
        self.org_a = Organizacao.objects.create(nome='Org A')
        self.org_b = Organizacao.objects.create(nome='Org B')
        self.ana = criar_usuario('ana', self.org_a)
        self.carla = criar_usuario('carla', self.org_a)
        self.beto = criar_usuario('beto', self.org_b)
        self.t_ana = Tarefa.objects.create(
            user=self.ana, organizacao=self.org_a, titulo='Tarefa da Ana')
        self.t_carla = Tarefa.objects.create(
            user=self.carla, organizacao=self.org_a, titulo='Tarefa da Carla')
        self.t_beto = Tarefa.objects.create(
            user=self.beto, organizacao=self.org_b, titulo='Tarefa do Beto')


class ApiTests(DadosBase, APITestCase):

    def test_sem_login_nao_acessa(self):
        r = self.client.get(reverse('api_tarefas'))
        self.assertIn(r.status_code, (401, 403))

    def test_usuario_sem_perfil_recebe_403(self):
        sem_perfil = User.objects.create_user('sem', password='senha12345')
        self.client.force_authenticate(sem_perfil)
        self.assertEqual(self.client.get(reverse('api_tarefas')).status_code, 403)

    def test_lista_so_as_tarefas_da_propria_organizacao(self):
        self.client.force_authenticate(self.ana)
        r = self.client.get(reverse('api_tarefas'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            sorted(t['titulo'] for t in r.json()),
            ['Tarefa da Ana', 'Tarefa da Carla'],
        )

    def test_detalhe_de_outra_organizacao_da_404(self):
        self.client.force_authenticate(self.ana)
        r = self.client.get(reverse('api_tarefa_detalhe', args=[self.t_beto.pk]))
        self.assertEqual(r.status_code, 404)

    def test_detalhe_de_colega_da_mesma_organizacao_da_200(self):
        self.client.force_authenticate(self.ana)
        r = self.client.get(reverse('api_tarefa_detalhe', args=[self.t_carla.pk]))
        self.assertEqual(r.status_code, 200)

    def test_nao_apaga_nem_edita_tarefa_de_outra_organizacao(self):
        self.client.force_authenticate(self.ana)
        url = reverse('api_tarefa_detalhe', args=[self.t_beto.pk])
        self.assertEqual(self.client.delete(url).status_code, 404)
        self.assertEqual(
            self.client.patch(url, {'titulo': 'Hackeada'}, format='json').status_code, 404)
        self.t_beto.refresh_from_db()
        self.assertEqual(self.t_beto.titulo, 'Tarefa do Beto')

    def test_criar_tarefa_grava_na_organizacao_do_usuario(self):
        self.client.force_authenticate(self.ana)
        r = self.client.post(reverse('api_tarefas'), {'titulo': 'Nova tarefa'}, format='json')
        self.assertEqual(r.status_code, 201)
        nova = Tarefa.objects.get(titulo='Nova tarefa')
        self.assertEqual(nova.organizacao, self.org_a)
        self.assertEqual(nova.user, self.ana)

    def test_nao_aceita_projeto_de_outra_organizacao(self):
        proj_b = Projeto.objects.create(
            nome='Proj B', dono=self.beto.perfil, organizacao=self.org_b)
        self.client.force_authenticate(self.ana)
        r = self.client.post(reverse('api_tarefas'), {
            'titulo': 'Invasora', 'projeto': proj_b.pk}, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertFalse(Tarefa.objects.filter(titulo='Invasora').exists())

    def test_titulo_curto_retorna_400(self):
        self.client.force_authenticate(self.ana)
        r = self.client.post(reverse('api_tarefas'), {'titulo': 'ab'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_prazo_anterior_ao_projeto_retorna_400(self):
        projeto = Projeto.objects.create(
            nome='P', dono=self.ana.perfil, organizacao=self.org_a)
        ontem = timezone.localdate() - timedelta(days=1)
        self.client.force_authenticate(self.ana)
        r = self.client.post(reverse('api_tarefas'), {
            'titulo': 'Com prazo', 'projeto': projeto.pk, 'prazo': ontem.isoformat(),
        }, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertIn('prazo', r.json())

    def test_nao_conclui_com_dependencia_pendente(self):
        Dependencia.objects.create(
            tarefa=self.t_carla, depende_de=self.t_ana, organizacao=self.org_a)
        self.client.force_authenticate(self.ana)
        r = self.client.patch(
            reverse('api_tarefa_detalhe', args=[self.t_carla.pk]),
            {'concluida': True}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_ciclo_de_dependencia_retorna_400(self):
        Dependencia.objects.create(
            tarefa=self.t_carla, depende_de=self.t_ana, organizacao=self.org_a)
        self.client.force_authenticate(self.ana)
        r = self.client.post(reverse('api_dependencias'), {
            'tarefa': self.t_ana.pk, 'depende_de': self.t_carla.pk}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_dependencia_entre_organizacoes_retorna_400(self):
        self.client.force_authenticate(self.ana)
        r = self.client.post(reverse('api_dependencias'), {
            'tarefa': self.t_ana.pk, 'depende_de': self.t_beto.pk}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_projetos_isolados_e_gravados_na_organizacao(self):
        Projeto.objects.create(nome='Proj B', dono=self.beto.perfil, organizacao=self.org_b)
        self.client.force_authenticate(self.ana)
        r = self.client.post(reverse('api_projetos'), {'nome': 'Proj A'}, format='json')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Projeto.objects.get(nome='Proj A').organizacao, self.org_a)
        nomes = [p['nome'] for p in self.client.get(reverse('api_projetos')).json()]
        self.assertEqual(nomes, ['Proj A'])

    def test_subtarefa_de_tarefa_de_outra_organizacao_retorna_400(self):
        self.client.force_authenticate(self.ana)
        r = self.client.post(reverse('api_subtarefas'), {
            'tarefa': self.t_beto.pk, 'titulo': 'Sub invasora'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_subtarefa_e_dependencia_de_outra_organizacao_dao_404(self):
        sub_b = Subtarefa.objects.create(
            tarefa=self.t_beto, organizacao=self.org_b, titulo='Sub do Beto')
        t2_b = Tarefa.objects.create(user=self.beto, organizacao=self.org_b, titulo='Outra do Beto')
        dep_b = Dependencia.objects.create(
            tarefa=t2_b, depende_de=self.t_beto, organizacao=self.org_b)
        self.client.force_authenticate(self.ana)
        self.assertEqual(
            self.client.get(reverse('api_subtarefa_detalhe', args=[sub_b.pk])).status_code, 404)
        self.assertEqual(
            self.client.get(reverse('api_dependencia_detalhe', args=[dep_b.pk])).status_code, 404)


class ModelTests(DadosBase, TestCase):

    def test_dependencia_entre_organizacoes_e_recusada(self):
        with self.assertRaises(ValidationError):
            Dependencia.objects.create(
                tarefa=self.t_ana, depende_de=self.t_beto, organizacao=self.org_a)

    def test_tarefa_com_projeto_de_outra_organizacao_e_recusada(self):
        proj_b = Projeto.objects.create(nome='Proj B', dono=self.beto.perfil, organizacao=self.org_b)
        with self.assertRaises(ValidationError):
            Tarefa.objects.create(
                user=self.ana, organizacao=self.org_a, titulo='Misturada', projeto=proj_b)

    def test_nao_conclui_tarefa_com_dependencia_pendente(self):
        Dependencia.objects.create(
            tarefa=self.t_carla, depende_de=self.t_ana, organizacao=self.org_a)
        self.t_carla.concluida = True
        with self.assertRaises(ValidationError):
            self.t_carla.save()

    def test_ciclo_e_recusado_no_model(self):
        Dependencia.objects.create(
            tarefa=self.t_carla, depende_de=self.t_ana, organizacao=self.org_a)
        with self.assertRaises(ValidationError):
            Dependencia.objects.create(
                tarefa=self.t_ana, depende_de=self.t_carla, organizacao=self.org_a)


class WebIsolamentoTests(DadosBase, TestCase):
    """Roteiro de isolamento da Aula 14 (slide 18)."""

    def entrar(self, nome):
        self.assertTrue(self.client.login(username=nome, password='senha12345'))

    def test_lista_mostra_so_a_organizacao_do_usuario(self):
        self.entrar('ana')
        r = self.client.get(reverse('home'))
        self.assertContains(r, 'Tarefa da Ana')
        self.assertContains(r, 'Tarefa da Carla')
        self.assertNotContains(r, 'Tarefa do Beto')

    def test_concluir_e_deletar_tarefa_de_outra_org_da_404(self):
        self.entrar('ana')
        r1 = self.client.post(reverse('concluir_tarefa', args=[self.t_beto.pk]))
        r2 = self.client.post(reverse('deletar_tarefa', args=[self.t_beto.pk]))
        self.assertEqual(r1.status_code, 404)
        self.assertEqual(r2.status_code, 404)
        self.t_beto.refresh_from_db()
        self.assertFalse(self.t_beto.concluida)

    def test_concluir_tarefa_bloqueada_pela_tela_nao_conclui(self):
        Dependencia.objects.create(
            tarefa=self.t_carla, depende_de=self.t_ana, organizacao=self.org_a)
        self.entrar('ana')
        self.client.post(reverse('concluir_tarefa', args=[self.t_carla.pk]))
        self.t_carla.refresh_from_db()
        self.assertFalse(self.t_carla.concluida)

    def test_criar_tarefa_grava_com_a_organizacao_do_usuario(self):
        self.entrar('ana')
        r = self.client.post(reverse('home'), {'form_type': 'tarefa', 'titulo': 'Nova da Ana'})
        self.assertEqual(r.status_code, 302)
        nova = Tarefa.objects.get(titulo='Nova da Ana')
        self.assertEqual(nova.organizacao, self.org_a)
        self.assertEqual(nova.user, self.ana)

    def test_selects_dos_formularios_mostram_so_opcoes_da_organizacao(self):
        Projeto.objects.create(nome='Proj A', dono=self.ana.perfil, organizacao=self.org_a)
        Projeto.objects.create(nome='Proj B', dono=self.beto.perfil, organizacao=self.org_b)
        self.entrar('ana')
        r = self.client.get(reverse('home'))
        projetos = [p.nome for p in r.context['tarefa_form'].fields['projeto'].queryset]
        self.assertEqual(projetos, ['Proj A'])
        tarefas = {t.titulo for t in r.context['dependencia_form'].fields['tarefa'].queryset}
        self.assertEqual(tarefas, {'Tarefa da Ana', 'Tarefa da Carla'})

    def test_nao_cria_tarefa_com_projeto_de_outra_organizacao(self):
        proj_b = Projeto.objects.create(nome='Proj B', dono=self.beto.perfil, organizacao=self.org_b)
        self.entrar('ana')
        self.client.post(reverse('home'), {
            'form_type': 'tarefa', 'titulo': 'Invasora', 'projeto': proj_b.pk})
        self.assertFalse(Tarefa.objects.filter(titulo='Invasora').exists())

    def test_usuario_sem_perfil_recebe_403(self):
        User.objects.create_user('sem', password='senha12345')
        self.entrar('sem')
        self.assertEqual(self.client.get(reverse('home')).status_code, 403)

    def test_cadastro_cria_organizacao_e_perfil(self):
        r = self.client.post(reverse('register'), {
            'username': 'novo', 'password1': 'Senha!Forte123', 'password2': 'Senha!Forte123'})
        self.assertEqual(r.status_code, 302)
        perfil = Perfil.objects.get(usuario__username='novo')
        self.assertEqual(perfil.organizacao.nome, 'Organização de novo')
from datetime import timedelta
import csv
import io

from django.db import connection
from django.test.utils import CaptureQueriesContext

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from .models import Organizacao, Perfil, Projeto, Tarefa, Subtarefa, Dependencia


def criar_usuario(nome, org, papel=Perfil.OPERADOR):
    usuario = User.objects.create_user(nome, password='senha12345')
    Perfil.objects.create(usuario=usuario, organizacao=org, papel=papel)
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

class DashboardBase(TestCase):
    """Org A: 3 tarefas (1 concluída, 1 atrasada, 1 no prazo). Org B: 5 tarefas."""

    def setUp(self):
        self.org_a = Organizacao.objects.create(nome='Org A')
        self.org_b = Organizacao.objects.create(nome='Org B')
        self.ana = criar_usuario('ana', self.org_a, Perfil.ADMIN)
        self.otavio = criar_usuario('otavio', self.org_a, Perfil.OPERADOR)
        self.beto = criar_usuario('beto', self.org_b, Perfil.ADMIN)
        ontem = timezone.localdate() - timedelta(days=1)
        self.projeto = Projeto.objects.create(
            nome='Projeto Alfa', dono=self.ana.perfil, organizacao=self.org_a)
        self.concluida = Tarefa.objects.create(
            user=self.ana, organizacao=self.org_a, titulo='A concluída',
            concluida=True, projeto=self.projeto)
        Tarefa.objects.create(
            user=self.ana, organizacao=self.org_a, titulo='A atrasada', prazo=ontem)
        Tarefa.objects.create(user=self.ana, organizacao=self.org_a, titulo='A no prazo')
        for i in range(5):
            Tarefa.objects.create(
                user=self.beto, organizacao=self.org_b, titulo=f'B tarefa {i}')

    def entrar(self, nome):
        self.assertTrue(self.client.login(username=nome, password='senha12345'))


class DashboardTests(DashboardBase):

    def test_total_so_da_organizacao(self):
        self.entrar('ana')
        r = self.client.get(reverse('dashboard'))
        self.assertEqual(r.context['kpis']['total'], 3)
        self.entrar('beto')
        r = self.client.get(reverse('dashboard'))
        self.assertEqual(r.context['kpis']['total'], 5)

    def test_kpis_detalhados(self):
        self.entrar('ana')
        k = self.client.get(reverse('dashboard')).context['kpis']
        self.assertEqual(
            (k['concluidas'], k['pendentes'], k['atrasadas'], k['responsaveis']),
            (1, 2, 1, 1))

    def test_filtro_de_periodo(self):
        Tarefa.objects.filter(pk=self.concluida.pk).update(
            criada_em=timezone.now() - timedelta(days=60))
        corte = (timezone.localdate() - timedelta(days=30)).isoformat()
        self.entrar('ana')
        r = self.client.get(reverse('dashboard'), {'inicio': corte})
        self.assertEqual(r.context['kpis']['total'], 2)
        r = self.client.get(reverse('dashboard'), {'fim': corte})
        self.assertEqual(r.context['kpis']['total'], 1)

    def test_data_invalida_nao_quebra(self):
        self.entrar('ana')
        r = self.client.get(reverse('dashboard'), {'inicio': 'abc'})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context['form'].errors)
        self.assertEqual(r.context['kpis']['total'], 3)

    def test_inicio_depois_do_fim_mostra_erro(self):
        self.entrar('ana')
        r = self.client.get(reverse('dashboard'), {'inicio': '2026-02-01', 'fim': '2026-01-01'})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context['form'].errors)

    def test_dashboard_vazio_nao_quebra(self):
        org_c = Organizacao.objects.create(nome='Org C')
        criar_usuario('cida', org_c, Perfil.ADMIN)
        self.entrar('cida')
        r = self.client.get(reverse('dashboard'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['kpis']['total'], 0)
        self.assertEqual(r.context['ranking'], [])
        self.assertEqual(r.context['por_mes'], [])

    def test_ranking_so_da_organizacao(self):
        self.entrar('ana')
        r = self.client.get(reverse('dashboard'))
        self.assertEqual(
            r.context['ranking'],
            [{'projeto_id': self.projeto.pk, 'projeto__nome': 'Projeto Alfa',
              'total': 1, 'pendentes': 0}])

    def test_serie_mensal_soma_o_total(self):
        self.entrar('ana')
        r = self.client.get(reverse('dashboard'))
        self.assertEqual(sum(m['total'] for m in r.context['por_mes']), 3)

    def test_operador_nao_ve_serie_nem_exportacao(self):
        self.entrar('otavio')
        r = self.client.get(reverse('dashboard'))
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(r.context.get('por_mes'))
        self.assertFalse(r.context['pode_exportar'])

    def test_sem_login_redireciona(self):
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 302)

    def test_usuario_sem_perfil_recebe_403(self):
        User.objects.create_user('sem', password='senha12345')
        self.entrar('sem')
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 403)


class ExportacaoCsvTests(DashboardBase):

    def linhas(self, resposta):
        texto = resposta.content.decode('utf-8-sig')
        return list(csv.reader(io.StringIO(texto), delimiter=';'))

    def test_operador_nao_exporta(self):
        self.entrar('otavio')
        self.assertEqual(self.client.get(reverse('exportar_csv')).status_code, 403)

    def test_admin_exporta_so_a_propria_organizacao(self):
        self.entrar('ana')
        r = self.client.get(reverse('exportar_csv'))
        self.assertEqual(r.status_code, 200)
        self.assertIn('text/csv', r['Content-Type'])
        titulos = [linha[0] for linha in self.linhas(r)[1:]]
        self.assertEqual(sorted(titulos), ['A atrasada', 'A concluída', 'A no prazo'])

    def test_celula_com_formula_e_neutralizada(self):
        Tarefa.objects.create(user=self.ana, organizacao=self.org_a, titulo='=1+1')
        self.entrar('ana')
        titulos = [linha[0] for linha in self.linhas(self.client.get(reverse('exportar_csv')))]
        self.assertIn("'=1+1", titulos)

    def test_periodo_invalido_retorna_400(self):
        self.entrar('ana')
        r = self.client.get(reverse('exportar_csv'), {'inicio': 'abc'})
        self.assertEqual(r.status_code, 400)


class DashboardApiTests(DashboardBase):

    def test_admin_recebe_metricas_da_organizacao(self):
        self.entrar('ana')
        r = self.client.get(reverse('api_dashboard'))
        self.assertEqual(r.status_code, 200)
        dados = r.json()
        self.assertEqual(dados['kpis']['total'], 3)
        self.assertIn('por_mes', dados)

    def test_operador_nao_recebe_serie(self):
        self.entrar('otavio')
        dados = self.client.get(reverse('api_dashboard')).json()
        self.assertEqual(dados['kpis']['total'], 3)
        self.assertNotIn('por_mes', dados)

    def test_periodo_invalido_retorna_400(self):
        self.entrar('ana')
        r = self.client.get(reverse('api_dashboard'), {'fim': 'abc'})
        self.assertEqual(r.status_code, 400)

    def test_sem_login_nao_acessa(self):
        self.assertIn(self.client.get(reverse('api_dashboard')).status_code, (401, 403))


class DesempenhoTests(DashboardBase):
    """Trava o N+1: o número de consultas não pode crescer com os dados."""

    def contar(self, url):
        with CaptureQueriesContext(connection) as ctx:
            r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        return len(ctx)

    def adicionar_tarefas_encadeadas(self, quantidade):
        anterior = Tarefa.objects.filter(organizacao=self.org_a, concluida=False).first()
        for i in range(quantidade):
            nova = Tarefa.objects.create(
                user=self.ana, organizacao=self.org_a, titulo=f'Extra {i}',
                projeto=self.projeto)
            Dependencia.objects.create(
                tarefa=nova, depende_de=anterior, organizacao=self.org_a)
            anterior = nova

    def test_home_nao_tem_n_mais_1(self):
        self.entrar('ana')
        antes = self.contar(reverse('home'))
        self.adicionar_tarefas_encadeadas(10)
        self.assertEqual(self.contar(reverse('home')), antes)

    def test_exportacao_nao_tem_n_mais_1(self):
        self.entrar('ana')
        antes = self.contar(reverse('exportar_csv'))
        self.adicionar_tarefas_encadeadas(10)
        self.assertEqual(self.contar(reverse('exportar_csv')), antes)

class SuperusuarioTests(TestCase):

    def setUp(self):
        self.root = User.objects.create_superuser('root', 'root@exemplo.com', 'senha12345')
        self.assertTrue(self.client.login(username='root', password='senha12345'))

    def test_superusuario_sem_perfil_acessa_telas_e_ganha_perfil_admin(self):
        self.assertEqual(self.client.get(reverse('home')).status_code, 200)
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 200)
        perfil = Perfil.objects.get(usuario=self.root)
        self.assertEqual(perfil.papel, Perfil.ADMIN)
        self.assertEqual(perfil.organizacao.nome, 'Organização padrão')

    def test_perfil_nao_e_duplicado_em_acessos_seguintes(self):
        self.client.get(reverse('home'))
        self.client.get(reverse('home'))
        self.assertEqual(Perfil.objects.filter(usuario=self.root).count(), 1)

    def test_superusuario_nao_ve_dados_de_outra_organizacao(self):
        org = Organizacao.objects.create(nome='Outra')
        dona = criar_usuario('dona', org)
        Tarefa.objects.create(user=dona, organizacao=org, titulo='Tarefa alheia')
        self.assertNotContains(self.client.get(reverse('home')), 'Tarefa alheia')
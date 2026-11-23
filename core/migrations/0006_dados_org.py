from django.db import migrations


def preencher_organizacao_padrao(apps, schema_editor):
    Organizacao = apps.get_model('core', 'Organizacao')
    Membro = apps.get_model('core', 'Membro')
    Projeto = apps.get_model('core', 'Projeto')
    Tarefa = apps.get_model('core', 'Tarefa')
    Subtarefa = apps.get_model('core', 'Subtarefa')
    Dependencia = apps.get_model('core', 'Dependencia')
    User = apps.get_model('auth', 'User')

    org, _ = Organizacao.objects.get_or_create(nome='Organização padrão')

    for modelo in (Membro, Projeto, Tarefa, Subtarefa, Dependencia):
        modelo.objects.filter(organizacao__isnull=True).update(organizacao=org)

    # Usuários sem vínculo recebem o Membro na organização padrão
    for user in User.objects.filter(membro__isnull=True):
        Membro.objects.create(user=user, organizacao=org)

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_org_obrigatoria'),
    ]

    operations = [
        migrations.RunPython(preencher_organizacao_padrao,
                             migrations.RunPython.noop),
    ]

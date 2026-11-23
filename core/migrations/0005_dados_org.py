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

    # Usuários sem vínculo (inclusive superusuário) recebem Membro na org padrão
    for user in User.objects.filter(membro__isnull=True):
        Membro.objects.create(user=user, organizacao=org)

    for modelo in (Membro, Projeto, Tarefa, Subtarefa, Dependencia):
        modelo.objects.filter(organizacao__isnull=True).update(organizacao=org)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_organizacao_membro'),
    ]

    operations = [
        migrations.RunPython(preencher_organizacao_padrao,
                             migrations.RunPython.noop),
    ]
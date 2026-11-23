from django.conf import settings
from django.db import migrations


def org_padrao(apps, schema_editor):
    Organizacao = apps.get_model('core', 'Organizacao')
    Perfil = apps.get_model('core', 'Perfil')
    Projeto = apps.get_model('core', 'Projeto')
    Tarefa = apps.get_model('core', 'Tarefa')
    Subtarefa = apps.get_model('core', 'Subtarefa')
    Dependencia = apps.get_model('core', 'Dependencia')
    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))

    modelos = [Perfil, Projeto, Tarefa, Subtarefa, Dependencia]
    if not (User.objects.exists() or any(m.objects.exists() for m in modelos)):
        return  # banco vazio: nada a migrar

    org, _ = Organizacao.objects.get_or_create(nome='Organização padrão')

    # todo usuário existente (inclusive superusuário) ganha um Perfil
    com_perfil = Perfil.objects.values_list('usuario_id', flat=True)
    for usuario in User.objects.exclude(pk__in=list(com_perfil)):
        Perfil.objects.create(usuario=usuario, organizacao=org)

    for modelo in modelos:
        modelo.objects.filter(organizacao__isnull=True).update(organizacao=org)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_organizacao_perfil'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(org_padrao, migrations.RunPython.noop),
    ]
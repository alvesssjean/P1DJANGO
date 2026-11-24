from django.db import migrations, models


def promover_existentes(apps, schema_editor):
    Perfil = apps.get_model('core', 'Perfil')
    Perfil.objects.update(papel='admin')


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_membro_para_perfil'),
    ]

    operations = [
        migrations.AddField(
            model_name='perfil',
            name='papel',
            field=models.CharField(
                choices=[('admin', 'Administrador'), ('operador', 'Operador')],
                default='operador', max_length=10,
            ),
        ),
        migrations.RunPython(promover_existentes, migrations.RunPython.noop),
    ]
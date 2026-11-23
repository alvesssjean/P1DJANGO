import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def _fk_org():
    return models.ForeignKey(
        null=True, on_delete=django.db.models.deletion.PROTECT, to='core.organizacao'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_tarefa_prazo'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Organizacao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=120)),
                ('criada_em', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'organização',
                'verbose_name_plural': 'organizações',
            },
        ),
        # Membro -> Perfil (mantém os dados existentes)
        migrations.RenameModel(old_name='Membro', new_name='Perfil'),
        migrations.RenameField(model_name='perfil', old_name='user', new_name='usuario'),
        migrations.AlterField(
            model_name='perfil',
            name='usuario',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
        # Etapa 1: FK de organização permitindo nulo
        migrations.AddField(model_name='perfil', name='organizacao', field=_fk_org()),
        migrations.AddField(model_name='projeto', name='organizacao', field=_fk_org()),
        migrations.AddField(model_name='tarefa', name='organizacao', field=_fk_org()),
        migrations.AddField(model_name='subtarefa', name='organizacao', field=_fk_org()),
        migrations.AddField(model_name='dependencia', name='organizacao', field=_fk_org()),
    ]
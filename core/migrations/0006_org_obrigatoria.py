import django.db.models.deletion
from django.db import migrations, models


def _fk_org():
    return models.ForeignKey(
        on_delete=django.db.models.deletion.PROTECT, to='core.organizacao'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_dados_org'),
    ]

    operations = [
        # Etapa 3: FK obrigatória
        migrations.AlterField(model_name='perfil', name='organizacao', field=_fk_org()),
        migrations.AlterField(model_name='projeto', name='organizacao', field=_fk_org()),
        migrations.AlterField(model_name='tarefa', name='organizacao', field=_fk_org()),
        migrations.AlterField(model_name='subtarefa', name='organizacao', field=_fk_org()),
        migrations.AlterField(model_name='dependencia', name='organizacao', field=_fk_org()),
    ]
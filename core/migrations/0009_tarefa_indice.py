from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_perfil_papel'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='tarefa',
            index=models.Index(
                fields=['organizacao', 'criada_em'], name='tarefa_org_criada_idx'),
        ),
    ]
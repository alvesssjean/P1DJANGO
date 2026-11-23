import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_org_obrigatoria'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(old_name='Membro', new_name='Perfil'),
        migrations.RenameField(model_name='perfil', old_name='user', new_name='usuario'),
        migrations.AlterField(
            model_name='perfil',
            name='usuario',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
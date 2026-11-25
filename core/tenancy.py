from django.core.exceptions import ObjectDoesNotExist, PermissionDenied

from .models import Organizacao, Perfil

ORGANIZACAO_PADRAO = 'Organização padrão'


def _perfil_do_superusuario(user):
    """O superusuário (dono do sistema) ganha Perfil de administrador na
    organização padrão no primeiro acesso, em vez de receber 403."""
    org = Organizacao.objects.filter(nome=ORGANIZACAO_PADRAO).first()
    if org is None:
        org = Organizacao.objects.create(nome=ORGANIZACAO_PADRAO)
    perfil, _ = Perfil.objects.get_or_create(
        usuario=user, defaults={'organizacao': org, 'papel': Perfil.ADMIN})
    return perfil


def org_do_usuario(user):
    """Organização do usuário, ou None (anônimo ou sem Perfil)."""
    if not user.is_authenticated:
        return None
    try:
        return user.perfil.organizacao
    except ObjectDoesNotExist:
        if user.is_superuser:
            return _perfil_do_superusuario(user).organizacao
        return None


def org_atual(request):
    """Único lugar que define a organização da requisição.

    Nunca confie na organização vinda da URL ou de formulário.
    Usuário sem Perfil (que não seja superusuário) recebe 403.
    """
    org = org_do_usuario(request.user)
    if org is None:
        raise PermissionDenied('Este usuário não está vinculado a nenhuma organização.')
    return org
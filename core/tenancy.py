from django.core.exceptions import ObjectDoesNotExist, PermissionDenied


def org_do_usuario(user):
    """Organização do usuário, ou None (anônimo ou sem Perfil)."""
    if not user.is_authenticated:
        return None
    try:
        return user.perfil.organizacao
    except ObjectDoesNotExist:
        return None


def org_atual(request):
    """Único lugar que define a organização da requisição.

    Nunca confie na organização vinda da URL ou de formulário.
    Sem Perfil (ex.: superusuário novo), responde 403 até a Aula 15.
    """
    org = org_do_usuario(request.user)
    if org is None:
        raise PermissionDenied('Este usuário não está vinculado a nenhuma organização.')
    return org
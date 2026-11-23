from django.core.exceptions import ObjectDoesNotExist, PermissionDenied


def org_atual(request):
    """Único lugar que define a organização da requisição.

    Nunca confie na organização vinda da URL ou de formulário.
    """
    try:
        return request.user.membro.organizacao
    except ObjectDoesNotExist:
        # Ex.: superusuário sem Membro (comportamento definitivo na Aula 15)
        raise PermissionDenied('Este usuário não está vinculado a nenhuma organização.')

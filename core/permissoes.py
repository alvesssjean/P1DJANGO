from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .tenancy import org_atual


def papel_requerido(*papeis):
    """Exige login, Perfil e um dos papéis informados (senão, 403)."""
    def decorador(view):
        @wraps(view)
        def envolvida(request, *args, **kwargs):
            org_atual(request)  # 403 se o usuário não tem Perfil
            if request.user.perfil.papel not in papeis:
                raise PermissionDenied('Seu papel não permite esta ação.')
            return view(request, *args, **kwargs)
        return login_required(envolvida)
    return decorador
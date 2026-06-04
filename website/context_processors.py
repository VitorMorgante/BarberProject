from website.models import Barbeiro

def user_roles(request):
    if not request.user.is_authenticated:
        return {
            'is_cliente': False,
            'is_barbeiro': False,
            'is_admin': False
        }
    
    user = request.user
    
    # Check Admin: Superuser, Staff or PerfilUsuario.tipo_usuario == 'administrador'
    is_admin = user.is_superuser or user.is_staff or (
        hasattr(user, 'perfil') and user.perfil.tipo_usuario.lower() == 'administrador'
    )
    
    # Check Barbeiro: PerfilUsuario.tipo_usuario == 'barbeiro' OR has a related Barbeiro record
    is_barbeiro = False
    if hasattr(user, 'perfil') and user.perfil.tipo_usuario.lower() == 'barbeiro':
        is_barbeiro = True
    elif Barbeiro.objects.filter(usuario=user).exists():
        is_barbeiro = True
        
    # Check Cliente: if not admin and not barber, defaults to client
    is_cliente = not is_admin and not is_barbeiro
    
    return {
        'is_cliente': is_cliente,
        'is_barbeiro': is_barbeiro,
        'is_admin': is_admin
    }

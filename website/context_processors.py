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


def brand_context(request):
    """Disponibiliza os dados centrais da marca Barber Heitor para todos os templates."""
    from django.conf import settings
    return {
        'BARBER_NAME': getattr(settings, 'BARBER_NAME', 'Barber Heitor'),
        'BARBER_SHORT_NAME': getattr(settings, 'BARBER_SHORT_NAME', 'Barber Heitor'),
        'BARBER_SLOGAN': getattr(settings, 'BARBER_SLOGAN', 'Seu estilo. Sua assinatura.'),
        'BARBER_PHONE': getattr(settings, 'BARBER_PHONE', '(44) 9102-2176'),
        'BARBER_PHONE_RAW': getattr(settings, 'BARBER_PHONE_RAW', '554491022176'),
        'BARBER_EMAIL': getattr(settings, 'BARBER_EMAIL', 'contato@barberheitor.com.br'),
        'BARBER_INSTAGRAM': getattr(settings, 'BARBER_INSTAGRAM', 'barberheitor_oficial'),
        'BARBER_ADDRESS': getattr(settings, 'BARBER_ADDRESS', 'Rua Terezinha Fortes Martins, 136, Jardim Progresso, Paranavaí - PR'),
        'BARBER_HOURS': getattr(settings, 'BARBER_HOURS', 'Seg a Sáb: 08:00 às 21:00'),
    }


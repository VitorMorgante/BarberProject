from website.models import Barbeiro

def user_roles(request):
    if not request.user.is_authenticated:
        return {
            'is_cliente': False,
            'is_barbeiro': False,
            'is_admin': False
        }
    
    user = request.user
    
    # Heitor é o dono e barbeiro: possui capacidades totais de administrador
    is_heitor = (
        'heitor' in user.username.lower() or
        Barbeiro.objects.filter(usuario=user, nome__icontains='heitor').exists() or
        user.email.lower() == 'heitor.pontes@barberheitor.com.br'
    )

    # Check Admin: Superuser, Staff, PerfilUsuario.tipo_usuario == 'administrador' ou Heitor
    is_admin = user.is_superuser or user.is_staff or (
        hasattr(user, 'perfil') and user.perfil.tipo_usuario.lower() == 'administrador'
    ) or is_heitor
    
    # Check Barbeiro: PerfilUsuario.tipo_usuario == 'barbeiro' OR has a related Barbeiro record OR is_heitor
    is_barbeiro = False
    barbeiro_logado = None
    if hasattr(user, 'perfil') and user.perfil.tipo_usuario.lower() == 'barbeiro':
        is_barbeiro = True
        barbeiro_logado = Barbeiro.objects.filter(usuario=user).first()
    elif Barbeiro.objects.filter(usuario=user).exists() or is_heitor:
        is_barbeiro = True
        barbeiro_logado = Barbeiro.objects.filter(usuario=user).first() or Barbeiro.objects.filter(nome__icontains='heitor').first()
        
    # Check Recepcionista: PerfilUsuario.tipo_usuario == 'recepcionista'
    is_recepcionista = False
    if hasattr(user, 'perfil') and user.perfil.tipo_usuario.lower() == 'recepcionista':
        is_recepcionista = True

    # Check Cliente: if not admin, not barber and not receptionist, defaults to client
    is_cliente = not is_admin and not is_barbeiro and not is_recepcionista
    
    return {
        'is_cliente': is_cliente,
        'is_barbeiro': is_barbeiro,
        'is_admin': is_admin,
        'is_recepcionista': is_recepcionista,
        'barbeiro_logado': barbeiro_logado
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
        'BARBER_INSTAGRAM': getattr(settings, 'BARBER_INSTAGRAM', 'barber.heitorr'),
        'BARBER_ADDRESS': getattr(settings, 'BARBER_ADDRESS', 'Rua Terezinha Fortes Martins, 136, Jardim Progresso, Paranavaí - PR'),
        'BARBER_HOURS': getattr(settings, 'BARBER_HOURS', 'Seg a Sáb: 08:00 às 21:30'),
    }


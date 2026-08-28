from django.utils import timezone
from website.models import RegistroAuditoria


class AuditService:
    """
    Serviço Central de Auditoria Administrativa e Rastreabilidade Operacional.
    """

    @staticmethod
    def registrar(usuario, acao: str, tabela: str, registro_id: str = '', valor_anterior: str = '', valor_novo: str = '', request=None):
        """
        Grava um registro permanente de auditoria no banco.
        """
        ip = None
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0].strip()
            else:
                ip = request.META.get('REMOTE_ADDR')

        return RegistroAuditoria.objects.create(
            usuario=usuario if (usuario and getattr(usuario, 'is_authenticated', False)) else None,
            acao=acao,
            tabela_afetada=tabela,
            registro_id=str(registro_id),
            valor_anterior=str(valor_anterior)[:500],
            valor_novo=str(valor_novo)[:500],
            ip=ip
        )

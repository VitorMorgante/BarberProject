import base64
import hashlib
import json
import uuid
from decimal import Decimal
from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from website.models import (
    Agendamento, Comanda, AssinaturaCliente,
    ConfiguracaoEstabelecimento, Pagamento, EventoWebhookPagamento
)


def _calcular_crc16(payload: str) -> str:
    """Calcula o CRC16-CCITT do payload PIX."""
    crc = 0xFFFF
    for char in payload:
        crc ^= (ord(char) << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc = crc << 1
            crc &= 0xFFFF
    return f"{crc:04X}"


def gerar_pix_copia_e_cola(chave: str, titular: str, cidade: str, valor: Decimal, txid: str = '') -> str:
    """
    Gera string oficial padrão BR Code (EMVCo) do Banco Central do Brasil para PIX.
    """
    titular_fmt = titular[:25].strip().upper()
    cidade_fmt = cidade[:15].strip().upper()
    valor_fmt = f"{valor:.2f}"
    txid_fmt = (txid or '***')[:25]

    # Payload Format Indicator (00)
    p00 = "000201"
    # Merchant Account Information (26)
    gui = "0014br.gov.bcb.pix"
    key = f"01{len(chave):02d}{chave}"
    p26 = f"26{len(gui + key):02d}{gui}{key}"
    # Merchant Category Code (52)
    p52 = "52040000"
    # Transaction Currency - BRL (53)
    p53 = "5303986"
    # Transaction Amount (54)
    p54 = f"54{len(valor_fmt):02d}{valor_fmt}"
    # Country Code - BR (58)
    p58 = "5802BR"
    # Merchant Name (59)
    p59 = f"59{len(titular_fmt):02d}{titular_fmt}"
    # Merchant City (60)
    p60 = f"60{len(cidade_fmt):02d}{cidade_fmt}"
    # Additional Data Field Template (62)
    ref = f"05{len(txid_fmt):02d}{txid_fmt}"
    p62 = f"62{len(ref):02d}{ref}"

    raw_payload = f"{p00}{p26}{p52}{p53}{p54}{p58}{p59}{p60}{p62}6304"
    crc = _calcular_crc16(raw_payload)
    return raw_payload + crc


class PaymentProviderInterface:
    def generate_pix(self, valor: Decimal, descricao: str, identificador_interno: str, expiracao_minutos: int) -> dict:
        raise NotImplementedError

    def get_payment_status(self, identificador_externo: str) -> dict:
        raise NotImplementedError


class MockPixProvider(PaymentProviderInterface):
    """
    Provider para desenvolvimento e testes: gera payload PIX real e simulador de QR Code.
    """
    def generate_pix(self, valor: Decimal, descricao: str, identificador_interno: str, expiracao_minutos: int) -> dict:
        config = ConfiguracaoEstabelecimento.get_solo()
        chave = config.chave_pix or getattr(settings, 'PIX_CHAVE', 'delacruzbarber@email.com')
        titular = config.titular_pix or getattr(settings, 'PIX_TITULAR', 'Delacruz Barber')
        cidade = config.cidade_pix or getattr(settings, 'PIX_CIDADE', 'Paranavai')

        pix_copia_cola = gerar_pix_copia_e_cola(
            chave=chave,
            titular=titular,
            cidade=cidade,
            valor=valor,
            txid=identificador_interno[:25].replace('-', '')
        )

        return {
            'identificador_externo': f"MOCK-PIX-{identificador_interno[:8].upper()}",
            'pix_copia_cola': pix_copia_cola,
            'qr_code_base64': '',
            'status': 'Aguardando',
            'raw_response': json.dumps({'gateway': 'mock', 'identificador': identificador_interno})
        }

    def get_payment_status(self, identificador_externo: str) -> dict:
        return {'status': 'Pago'}


class MercadoPagoProvider(PaymentProviderInterface):
    def generate_pix(self, valor: Decimal, descricao: str, identificador_interno: str, expiracao_minutos: int) -> dict:
        access_token = getattr(settings, 'PAYMENT_ACCESS_TOKEN', '')
        if not access_token:
            # Fallback para Mock se credencial não existir
            return MockPixProvider().generate_pix(valor, descricao, identificador_interno, expiracao_minutos)

        import requests
        headers = {
            'Authorization': f"Bearer {access_token}",
            'Content-Type': 'application/json',
            'X-Idempotency-Key': identificador_interno
        }
        expiracao = timezone.now() + timedelta(minutes=expiracao_minutos)
        payload = {
            'transaction_amount': float(valor),
            'description': descricao[:60],
            'payment_method_id': 'pix',
            'date_of_expiration': expiracao.strftime('%Y-%m-%dT%H:%M:%S.000-03:00'),
            'payer': {
                'email': 'cliente@delacruzbarber.com.br',
                'first_name': 'Cliente',
                'last_name': 'Delacruz'
            }
        }
        try:
            resp = requests.post('https://api.mercadopago.com/v1/payments', json=payload, headers=headers, timeout=10)
            data = resp.json()
            point_of_interaction = data.get('point_of_interaction', {}).get('transaction_data', {})
            return {
                'identificador_externo': str(data.get('id', '')),
                'pix_copia_cola': point_of_interaction.get('qr_code', ''),
                'qr_code_base64': point_of_interaction.get('qr_code_base64', ''),
                'status': 'Aguardando',
                'raw_response': json.dumps(data)
            }
        except Exception as e:
            return MockPixProvider().generate_pix(valor, descricao, identificador_interno, expiracao_minutos)

    def get_payment_status(self, identificador_externo: str) -> dict:
        access_token = getattr(settings, 'PAYMENT_ACCESS_TOKEN', '')
        if not access_token:
            return {'status': 'Pago'}
        import requests
        headers = {'Authorization': f"Bearer {access_token}"}
        try:
            resp = requests.get(f"https://api.mercadopago.com/v1/payments/{identificador_externo}", headers=headers, timeout=10)
            data = resp.json()
            mp_status = data.get('status')
            status_map = {
                'approved': 'Pago',
                'pending': 'Aguardando',
                'in_process': 'Aguardando',
                'rejected': 'Cancelado',
                'cancelled': 'Cancelado',
                'refunded': 'Reembolsado',
            }
            return {'status': status_map.get(mp_status, 'Aguardando'), 'raw': data}
        except Exception:
            return {'status': 'Aguardando'}


def get_payment_provider() -> PaymentProviderInterface:
    gateway = getattr(settings, 'PAYMENT_GATEWAY', 'mock').lower()
    if gateway == 'mercadopago' and getattr(settings, 'PAYMENT_ACCESS_TOKEN', ''):
        return MercadoPagoProvider()
    return MockPixProvider()


class PaymentService:
    @staticmethod
    def calcular_sinal_agendamento(servico, config: ConfiguracaoEstabelecimento = None) -> Decimal:
        """Calcula o valor do sinal obrigatório para reserva de agendamento."""
        config = config or ConfiguracaoEstabelecimento.get_solo()
        preco = Decimal(str(servico.preco))

        if config.tipo_sinal == ConfiguracaoEstabelecimento.TipoSinal.NENHUM:
            return Decimal('0.00')
        elif config.tipo_sinal == ConfiguracaoEstabelecimento.TipoSinal.PERCENTUAL:
            pct = config.valor_sinal or Decimal('30.00')
            return max(Decimal('0.00'), (preco * pct) / Decimal('100.00'))
        elif config.tipo_sinal == ConfiguracaoEstabelecimento.TipoSinal.FIXO:
            return min(preco, config.valor_sinal or Decimal('20.00'))
        elif config.tipo_sinal == ConfiguracaoEstabelecimento.TipoSinal.INTEGRAL:
            return preco
        return Decimal('0.00')

    @staticmethod
    @transaction.atomic
    def criar_pagamento_sinal(agendamento: Agendamento) -> Pagamento:
        """Gera cobrança PIX para o sinal de agendamento."""
        config = ConfiguracaoEstabelecimento.get_solo()
        valor_sinal = PaymentService.calcular_sinal_agendamento(agendamento.servico, config)

        if valor_sinal <= Decimal('0.00'):
            return None

        expiracao_minutos = config.minutos_expiracao_pix or 15
        expiracao_em = timezone.now() + timedelta(minutes=expiracao_minutos)
        identificador = str(uuid.uuid4())

        provider = get_payment_provider()
        res = provider.generate_pix(
            valor=valor_sinal,
            descricao=f"Sinal Agendamento #{agendamento.id} - {agendamento.servico.nome}",
            identificador_interno=identificador,
            expiracao_minutos=expiracao_minutos
        )

        pagamento = Pagamento.objects.create(
            identificador_interno=identificador,
            identificador_externo=res.get('identificador_externo'),
            agendamento=agendamento,
            valor=valor_sinal,
            tipo=Pagamento.Tipo.SINAL,
            metodo=Pagamento.Metodo.PIX,
            status=Pagamento.Status.AGUARDANDO,
            pix_copia_cola=res.get('pix_copia_cola', ''),
            qr_code_base64=res.get('qr_code_base64', ''),
            gateway=getattr(settings, 'PAYMENT_GATEWAY', 'mock'),
            payload_resposta=res.get('raw_response', ''),
            expiracao_em=expiracao_em,
        )
        return pagamento

    @staticmethod
    @transaction.atomic
    def confirmar_pagamento(pagamento_ou_id, payload: str = '') -> Pagamento:
        """
        Confirma o pagamento atomicamente, atualizando o agendamento/comanda/assinatura correspondente.
        É idempotente e protege contra processamento duplo.
        """
        if isinstance(pagamento_ou_id, Pagamento):
            pagamento = Pagamento.objects.select_for_update().get(pk=pagamento_ou_id.pk)
        else:
            pagamento = Pagamento.objects.select_for_update().get(identificador_interno=str(pagamento_ou_id))

        if pagamento.status == Pagamento.Status.PAGO:
            return pagamento  # Já processado com sucesso anteriormente

        pagamento.status = Pagamento.Status.PAGO
        pagamento.pago_em = timezone.now()
        if payload:
            pagamento.payload_resposta = payload
        pagamento.save()

        # 1. Se for Sinal de Agendamento -> Muda agendamento para Confirmado
        if pagamento.agendamento and pagamento.tipo in [Pagamento.Tipo.SINAL, Pagamento.Tipo.TOTAL]:
            agendamento = pagamento.agendamento
            if agendamento.status == Agendamento.Status.PENDENTE:
                agendamento.status = Agendamento.Status.CONFIRMADO
                agendamento.save(update_fields=['status', 'atualizado_em'])

        # 2. Se for Comanda -> Registra sinal_pago ou fecha
        if pagamento.comanda:
            comanda = pagamento.comanda
            if pagamento.tipo == Pagamento.Tipo.SINAL:
                comanda.sinal_pago = pagamento.valor
            comanda.recalcular()

        # 3. Se for Assinatura -> Ativa a assinatura
        if pagamento.assinatura:
            assinatura = pagamento.assinatura
            from website.services.subscription_service import SubscriptionService
            SubscriptionService.ativar_ou_renovar_assinatura(assinatura.cliente, assinatura.plano)

        return pagamento

    @staticmethod
    @transaction.atomic
    def processar_webhook(gateway: str, evento_id: str, payload_dict: dict) -> bool:
        """
        Processa webhook com verificação de idempotência em EventoWebhookPagamento.
        """
        evento_existente, created = EventoWebhookPagamento.objects.get_or_create(
            evento_id=str(evento_id),
            defaults={
                'gateway': gateway,
                'payload': json.dumps(payload_dict),
                'processado': False,
            }
        )

        if not created and evento_existente.processado:
            return True  # Já processado anteriormente

        # Identifica o pagamento via external_reference ou payment_id
        identificador = payload_dict.get('data', {}).get('id') or payload_dict.get('id') or evento_id

        pagamento = Pagamento.objects.filter(
            identificador_externo=str(identificador)
        ).first()

        if not pagamento and 'external_reference' in payload_dict:
            pagamento = Pagamento.objects.filter(
                identificador_interno=payload_dict['external_reference']
            ).first()

        if pagamento:
            PaymentService.confirmar_pagamento(pagamento, json.dumps(payload_dict))
            evento_existente.processado = True
            evento_existente.save()
            return True

        evento_existente.erro = "Pagamento não localizado no banco para este evento."
        evento_existente.save()
        return False

    @staticmethod
    @transaction.atomic
    def expirar_pagamentos_pendentes():
        """
        Cancela pagamentos com prazo de PIX expirado e libera agendamentos pendentes.
        """
        agora = timezone.now()
        expirados = Pagamento.objects.select_for_update().filter(
            status=Pagamento.Status.AGUARDANDO,
            expiracao_em__lt=agora
        )
        for pag in expirados:
            pag.status = Pagamento.Status.EXPIRADO
            pag.save()

            if pag.agendamento and pag.agendamento.status == Agendamento.Status.PENDENTE:
                pag.agendamento.status = Agendamento.Status.CANCELADO
                pag.agendamento.observacoes += " [Cancelado automaticamente por expiração de PIX do sinal]"
                pag.agendamento.save(update_fields=['status', 'observacoes', 'atualizado_em'])

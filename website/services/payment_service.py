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


def gerar_qr_code_base64(conteudo: str) -> str:
    """Gera imagem PNG codificada em Base64 do QR Code localmente sem vazar dados para serviços terceiros."""
    if not conteudo:
        return ''
    try:
        import qrcode
        from io import BytesIO
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(conteudo)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    except Exception:
        return ''


class PaymentProviderInterface:
    def generate_pix(self, valor: Decimal, descricao: str, identificador_interno: str, expiracao_minutos: int, agendamento=None) -> dict:
        raise NotImplementedError

    def get_payment_status(self, identificador_externo: str) -> dict:
        raise NotImplementedError


class MockPixProvider(PaymentProviderInterface):
    """
    Provider para desenvolvimento e testes: gera payload PIX real e simulador de QR Code.
    """
    def generate_pix(self, valor: Decimal, descricao: str, identificador_interno: str, expiracao_minutos: int, agendamento=None) -> dict:
        config = ConfiguracaoEstabelecimento.get_solo()
        chave = config.chave_pix or getattr(settings, 'PIX_CHAVE', '') or 'contato@barberheitor.com.br'
        titular = config.titular_pix or getattr(settings, 'PIX_TITULAR', 'Barber Heitor')
        cidade = config.cidade_pix or getattr(settings, 'PIX_CIDADE', 'Paranavai')

        pix_copia_cola = gerar_pix_copia_e_cola(
            chave=chave,
            titular=titular,
            cidade=cidade,
            valor=valor,
            txid=identificador_interno[:25].replace('-', '')
        )
        qr_code_base64 = gerar_qr_code_base64(pix_copia_cola)

        return {
            'identificador_externo': f"MOCK-PIX-{identificador_interno[:8].upper()}",
            'pix_copia_cola': pix_copia_cola,
            'qr_code_base64': qr_code_base64,
            'status': 'Aguardando',
            'raw_response': json.dumps({'gateway': 'mock', 'identificador': identificador_interno})
        }

    def get_payment_status(self, identificador_externo: str) -> dict:
        return {'status': 'Pago'}


class MercadoPagoProvider(PaymentProviderInterface):
    def generate_pix(self, valor: Decimal, descricao: str, identificador_interno: str, expiracao_minutos: int, agendamento=None) -> dict:
        access_token = getattr(settings, 'PAYMENT_ACCESS_TOKEN', '')
        if not access_token:
            if not settings.DEBUG:
                from django.core.exceptions import ImproperlyConfigured
                raise ImproperlyConfigured("PAYMENT_GATEWAY='mercadopago' configurado, mas PAYMENT_ACCESS_TOKEN não foi definido no ambiente de produção.")
            return MockPixProvider().generate_pix(valor, descricao, identificador_interno, expiracao_minutos, agendamento=agendamento)

        import requests
        headers = {
            'Authorization': f"Bearer {access_token}",
            'Content-Type': 'application/json',
            'X-Idempotency-Key': identificador_interno
        }
        expiracao = timezone.now() + timedelta(minutes=expiracao_minutos)
        
        # Payer data real e sanitizado
        payer_email = 'contato@barberheitor.com.br'
        payer_first = 'Cliente'
        payer_last = 'Barber Heitor'
        
        if agendamento and getattr(agendamento, 'cliente', None):
            cliente = agendamento.cliente
            if cliente.email and '@' in cliente.email:
                payer_email = cliente.email
            if cliente.nome:
                parts = cliente.nome.strip().split(' ', 1)
                payer_first = parts[0]
                payer_last = parts[1] if len(parts) > 1 else 'Cliente'

        payload = {
            'transaction_amount': float(valor),
            'description': descricao[:60],
            'payment_method_id': 'pix',
            'date_of_expiration': expiracao.strftime('%Y-%m-%dT%H:%M:%S.000-03:00'),
            'payer': {
                'email': payer_email,
                'first_name': payer_first,
                'last_name': payer_last
            }
        }
        try:
            resp = requests.post('https://api.mercadopago.com/v1/payments', json=payload, headers=headers, timeout=10)
            data = resp.json()
            point_of_interaction = data.get('point_of_interaction', {}).get('transaction_data', {})
            pix_copia_cola = point_of_interaction.get('qr_code', '')
            qr_code_base64 = point_of_interaction.get('qr_code_base64', '')
            
            if not qr_code_base64 and pix_copia_cola:
                qr_code_base64 = gerar_qr_code_base64(pix_copia_cola)

            return {
                'identificador_externo': str(data.get('id', '')),
                'pix_copia_cola': pix_copia_cola,
                'qr_code_base64': qr_code_base64,
                'status': 'Aguardando',
                'raw_response': json.dumps(data)
            }
        except Exception as e:
            if not settings.DEBUG:
                raise RuntimeError(f"Erro na comunicação com a API do Mercado Pago: {e}")
            return MockPixProvider().generate_pix(valor, descricao, identificador_interno, expiracao_minutos, agendamento=agendamento)

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
    if gateway == 'mercadopago':
        if not getattr(settings, 'PAYMENT_ACCESS_TOKEN', ''):
            if not settings.DEBUG:
                from django.core.exceptions import ImproperlyConfigured
                raise ImproperlyConfigured("Configuração inválida: PAYMENT_GATEWAY='mercadopago' sem PAYMENT_ACCESS_TOKEN em produção.")
            return MockPixProvider()
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
            expiracao_minutos=expiracao_minutos,
            agendamento=agendamento
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
    def processar_webhook(gateway: str, evento_id: str, payload_dict: dict, headers: dict = None) -> bool:
        """
        Processa webhook com verificação de idempotência em EventoWebhookPagamento,
        validação de assinatura e consulta de confirmação ativa ao gateway.
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

        # Validação de Assinatura HMAC-SHA256 para Mercado Pago se segredo configurado
        webhook_secret = getattr(settings, 'PAYMENT_WEBHOOK_SECRET', '')
        if gateway == 'mercadopago' and webhook_secret and headers:
            x_signature = headers.get('x-signature') or headers.get('X-Signature', '')
            if x_signature:
                try:
                    import hmac
                    parts = dict(item.split('=', 1) for item in x_signature.split(',') if '=' in item)
                    ts = parts.get('ts')
                    v1 = parts.get('v1')
                    data_id = str(payload_dict.get('data', {}).get('id') or payload_dict.get('id', ''))
                    manifest = f"id:{data_id};request-id:{headers.get('x-request-id', '')};ts:{ts};"
                    expected_signature = hmac.new(webhook_secret.encode('utf-8'), manifest.encode('utf-8'), hashlib.sha256).hexdigest()
                    if v1 != expected_signature:
                        evento_existente.erro = "Assinatura HMAC-SHA256 do webhook inválida."
                        evento_existente.save()
                        return False
                except Exception as ex:
                    evento_existente.erro = f"Falha na validação de assinatura: {ex}"
                    evento_existente.save()
                    return False

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
            # Em produção, se Mercado Pago possuir token, consulta API para validar status aprovado e valor
            access_token = getattr(settings, 'PAYMENT_ACCESS_TOKEN', '')
            if gateway == 'mercadopago' and access_token:
                try:
                    import requests
                    resp = requests.get(
                        f"https://api.mercadopago.com/v1/payments/{pagamento.identificador_externo}",
                        headers={'Authorization': f"Bearer {access_token}"},
                        timeout=8
                    )
                    if resp.status_code == 200:
                        mp_data = resp.json()
                        if mp_data.get('status') != 'approved':
                            evento_existente.erro = f"Status no Mercado Pago é '{mp_data.get('status')}', não 'approved'."
                            evento_existente.save()
                            return False
                        
                        tx_amount = Decimal(str(mp_data.get('transaction_amount', 0)))
                        if tx_amount < pagamento.valor:
                            evento_existente.erro = f"Valor pago (R$ {tx_amount}) é inferior ao esperado (R$ {pagamento.valor})."
                            evento_existente.save()
                            return False
                except Exception as e:
                    evento_existente.erro = f"Erro na consulta direta de confirmação ao gateway: {e}"
                    evento_existente.save()
                    return False

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

    @staticmethod
    def calcular_sinal_adaptativo(cliente, servico, config: ConfiguracaoEstabelecimento = None) -> Decimal:
        """
        Calcula o sinal adaptativo conforme o risco de no-show do cliente.
        Se o cliente tiver risco elevado (no-shows recorrentes), exige sinal maior (ex: 50%).
        """
        from website.services.agenda_inteligente_service import AgendaInteligenteService
        config = config or ConfiguracaoEstabelecimento.get_solo()
        sinal_padrao = PaymentService.calcular_sinal_agendamento(servico, config)

        if cliente:
            score_risco = AgendaInteligenteService.calcular_score_no_show(cliente)
            if score_risco >= 60:
                sinal_reforcado = (Decimal(str(servico.preco)) * Decimal('50.00')) / Decimal('100.00')
                return max(sinal_padrao, round(sinal_reforcado, 2))

        return sinal_padrao

    @staticmethod
    @transaction.atomic
    def registrar_pagamento_dividido(comanda: Comanda, pagamentos_info: list, gorjeta_valor: Decimal = Decimal('0.00'), barbeiro_gorjeta=None, usuario=None) -> Comanda:
        """
        Fecha a comanda dividindo o pagamento entre múltiplos métodos (PIX, Dinheiro, Cartão, Saldo Interno).
        Registra gorjeta separada (se informada) e valida se a soma dos pagamentos fecha exatamente o valor_total.
        """
        from website.models import PagamentoDividido, Gorjeta, TaxaMetodoPagamento, ContaCorrenteCliente, MovimentacaoContaCorrente
        comanda = Comanda.objects.select_for_update().get(pk=comanda.pk)
        comanda.recalcular()

        total_pago = sum(Decimal(str(p['valor'])) for p in pagamentos_info)
        if total_pago < comanda.valor_total:
            raise ValueError(f"Soma dos pagamentos (R$ {total_pago}) é inferior ao total da comanda (R$ {comanda.valor_total}).")

        # Limpa pagamentos parciais antigos se houver
        comanda.pagamentos_divididos.all().delete()

        for p in pagamentos_info:
            metodo = p['metodo']
            val = Decimal(str(p['valor']))

            # Busca taxa cadastrada
            taxa_obj = TaxaMetodoPagamento.objects.filter(metodo=metodo, ativo=True).first()
            taxa_pct = taxa_obj.taxa_percentual if taxa_obj else Decimal('0.00')
            taxa_fixa = taxa_obj.taxa_fixa_reais if taxa_obj else Decimal('0.00')
            valor_liq = val - ((val * taxa_pct) / Decimal('100.00')) - taxa_fixa

            # Se o pagamento for via Saldo Interno, debita da ContaCorrenteCliente
            if metodo == PagamentoDividido.Metodo.SALDO_INTERNO:
                conta = ContaCorrenteCliente.objects.select_for_update().filter(cliente=comanda.cliente).first()
                if not conta or conta.saldo < val:
                    raise ValueError(f"Saldo insuficiente na conta corrente do cliente (Disponível: R$ {getattr(conta, 'saldo', 0)}).")
                saldo_ant = conta.saldo
                conta.saldo -= val
                conta.save(update_fields=['saldo', 'atualizado_em'])
                MovimentacaoContaCorrente.objects.create(
                    conta_corrente=conta,
                    tipo=MovimentacaoContaCorrente.Tipo.DEBITO,
                    valor=val,
                    saldo_anterior=saldo_ant,
                    saldo_posterior=conta.saldo,
                    descricao=f"Pagamento na Comanda #{comanda.id}",
                    usuario=usuario
                )

            PagamentoDividido.objects.create(
                comanda=comanda,
                metodo=metodo,
                valor=val,
                taxa_percentual=taxa_pct,
                valor_liquido=max(Decimal('0.00'), valor_liq)
            )

        # Registra Gorjeta separada se houver
        if gorjeta_valor > Decimal('0.00'):
            barb_alvo = barbeiro_gorjeta or comanda.barbeiro
            Gorjeta.objects.create(
                comanda=comanda,
                barbeiro=barb_alvo,
                valor=gorjeta_valor,
                metodo_pagamento=pagamentos_info[0]['metodo'] if pagamentos_info else 'Pix',
                repassada=False
            )

        comanda.status = Comanda.Status.FECHADA
        comanda.fechada_em = timezone.now()
        comanda.metodo_pagamento = " / ".join(dict.fromkeys(p['metodo'].upper() for p in pagamentos_info))
        comanda.save()

        return comanda

    @staticmethod
    @transaction.atomic
    def estornar_pagamento_parcial(pagamento_id: int, valor_estorno: Decimal, motivo: str = '', usuario=None) -> Pagamento:
        """
        Executa estorno parcial ou total com registro de auditoria e ajuste financeiro.
        """
        from website.services.audit_service import AuditService
        pagamento = Pagamento.objects.select_for_update().get(pk=pagamento_id)
        if valor_estorno > pagamento.valor:
            raise ValueError("Valor de estorno não pode ser maior que o valor do pagamento original.")

        valor_antigo = pagamento.valor
        pagamento.status = Pagamento.Status.REEMBOLSADO if valor_estorno == pagamento.valor else Pagamento.Status.PAGO
        pagamento.valor = pagamento.valor - valor_estorno
        pagamento.save()

        AuditService.registrar(
            usuario=usuario,
            acao='estorno_realizado',
            tabela='Pagamento',
            registro_id=str(pagamento.id),
            valor_anterior=f"R$ {valor_antigo}",
            valor_novo=f"Estorno: R$ {valor_estorno} (Novo saldo: R$ {pagamento.valor}) - Motivo: {motivo}"
        )
        return pagamento

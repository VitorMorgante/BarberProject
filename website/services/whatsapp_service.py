import re
import urllib.parse
from django.conf import settings
from django.utils import timezone
from website.models import Agendamento, Notificacao, ListaEspera


class WhatsAppService:
    @staticmethod
    def sanitizar_telefone(telefone: str) -> str:
        """
        Sanitiza o telefone para o formato internacional aceito pelo WhatsApp (DDI 55 + DDD + Número).
        Ex: (44) 99190-0997 -> 5544991900997
        """
        numeros = re.sub(r'\D', '', telefone or '')
        if not numeros:
            return ''
        if len(numeros) in [10, 11] and not numeros.startswith('55'):
            numeros = '55' + numeros
        return numeros

    @staticmethod
    def gerar_link_click_to_chat(telefone: str, mensagem: str) -> str:
        """
        Gera link oficial do WhatsApp Click-to-Chat com texto codificado em UTF-8.
        """
        fone_limpo = WhatsAppService.sanitizar_telefone(telefone)
        if not fone_limpo:
            return '#'
        msg_encoded = urllib.parse.quote(mensagem)
        return f"https://wa.me/{fone_limpo}?text={msg_encoded}"

    @staticmethod
    def gerar_mensagem_barbeiro_chamar(agendamento: Agendamento) -> str:
        """
        Mensagem pré-formatada para o barbeiro chamar o cliente pelo WhatsApp.
        """
        cliente_nome = agendamento.cliente.nome.split()[0]
        data_str = agendamento.data.strftime('%d/%m')
        hora_str = agendamento.horario.strftime('%H:%M')
        return (
            f"Olá, {cliente_nome}! 👋 Aqui é da *Delacruz Barber*.\n\n"
            f"Passando para confirmar seu horário de *{agendamento.servico.nome}* hoje ({data_str}) "
            f"às *{hora_str}* com *{agendamento.barbeiro.nome}* 💈.\n\n"
            f"Estamos prontos para te receber! Qualquer imprevisto, só nos avisar por aqui. 👊"
        )

    @staticmethod
    def gerar_mensagem_lembrete_24h(agendamento: Agendamento) -> str:
        cliente_nome = agendamento.cliente.nome.split()[0]
        data_str = agendamento.data.strftime('%d/%m')
        hora_str = agendamento.horario.strftime('%H:%M')
        return (
            f"Olá, {cliente_nome}! 💈 Lembrete da *Delacruz Barber*:\n\n"
            f"Seu corte está agendado para amanhã, *{data_str}* às *{hora_str}* com *{agendamento.barbeiro.nome}*.\n"
            f"📍 Rua Terezinha Fortes Martins, 136 - Paranavaí PR.\n\n"
            f"Nos vemos em breve!"
        )

    @staticmethod
    def gerar_mensagem_vaga_waitlist(waitlist: ListaEspera, horario_str: str) -> str:
        cliente_nome = waitlist.cliente.nome.split()[0]
        data_str = waitlist.data_desejada.strftime('%d/%m')
        return (
            f"Fala {cliente_nome}! 🔥 Surgiu uma *vaga de encaixe* na *Delacruz Barber*!\n\n"
            f"📅 Data: *{data_str}*\n"
            f"⏰ Horário: *{horario_str}*\n"
            f"✂️ Serviço: *{waitlist.servico.nome}*\n\n"
            f"Acesse agora a Área do Cliente para garantir seu horário antes que outro cliente reserve!"
        )

    @staticmethod
    def enviar_whatsapp_api(telefone: str, mensagem: str) -> bool:
        """
        Envia mensagem via WhatsApp Cloud API / Provider se configurado em settings/env.
        Se não estiver configurado, retorna False (mantendo camada click-to-chat).
        """
        provider = getattr(settings, 'WHATSAPP_PROVIDER', 'none').lower()
        token = getattr(settings, 'WHATSAPP_API_TOKEN', '')
        phone_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', '')

        if provider != 'cloud_api' or not token or not phone_id:
            return False

        import requests
        fone_limpo = WhatsAppService.sanitizar_telefone(telefone)
        url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
        headers = {
            'Authorization': f"Bearer {token}",
            'Content-Type': 'application/json'
        }
        payload = {
            'messaging_product': 'whatsapp',
            'to': fone_limpo,
            'type': 'text',
            'text': {'body': mensagem}
        }
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            return resp.status_code in [200, 201]
        except Exception:
            return False

from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from datetime import date
from .models import (
    Servico, Barbeiro, Cliente, HorarioDisponivel, Agendamento,
    MensagemContato, PerfilUsuario, Feedback, FotoTrabalho,
    PlanoAssinatura, AssinaturaCliente, Produto, MovimentacaoEstoque,
    Comanda, ItemComanda, RegraComissao, MetaBarbeiro, RepasseComissao,
    ConfiguracaoEstabelecimento, ListaEspera, EstiloCorte, AnaliseEstilo,
    HistoricoVisualCliente
)


class ServicoForm(forms.ModelForm):
    class Meta:
        model = Servico
        exclude = ['usuario', 'cadastrado_em', 'atualizado_em']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'preco': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'duracao_minutos': forms.NumberInput(attrs={'class': 'form-control'}),
            'categoria': forms.TextInput(attrs={'class': 'form-control'}),
            'icone': forms.TextInput(attrs={'class': 'form-control'}),
            'ordem': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class BarbeiroForm(forms.ModelForm):
    class Meta:
        model = Barbeiro
        exclude = ['cadastrado_em', 'atualizado_em']
        widgets = {
            'usuario': forms.Select(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),
            'especialidade': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao_curta': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'imagem_url': forms.URLInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        exclude = ['usuario', 'cadastrado_em', 'atualizado_em']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class HorarioDisponivelForm(forms.ModelForm):
    class Meta:
        model = HorarioDisponivel
        exclude = ['usuario']
        widgets = {
            'barbeiro': forms.Select(attrs={'class': 'form-control'}),
            'horario': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'observacao': forms.TextInput(attrs={'class': 'form-control'}),
        }


class AgendamentoForm(forms.ModelForm):
    class Meta:
        model = Agendamento
        fields = ['cliente', 'servico', 'barbeiro', 'data', 'horario', 'status', 'observacoes']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'servico': forms.Select(attrs={'class': 'form-control'}),
            'barbeiro': forms.Select(attrs={'class': 'form-control'}),
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'horario': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_data(self):
        data_agendamento = self.cleaned_data.get('data')
        if data_agendamento and data_agendamento < date.today():
            raise ValidationError('Não é possível agendar em datas passadas.')
        return data_agendamento

    def clean(self):
        cleaned_data = super().clean()
        barbeiro = cleaned_data.get('barbeiro')
        data_agendamento = cleaned_data.get('data')
        horario = cleaned_data.get('horario')
        status = cleaned_data.get('status')

        if barbeiro and data_agendamento and horario and status != Agendamento.Status.CANCELADO:
            query = Agendamento.objects.filter(
                barbeiro=barbeiro,
                data=data_agendamento,
                horario=horario,
            ).exclude(status=Agendamento.Status.CANCELADO)

            if self.instance and self.instance.pk:
                query = query.exclude(pk=self.instance.pk)

            if query.exists():
                raise ValidationError('Este horário já está reservado para o barbeiro selecionado.')

            horario_valido = HorarioDisponivel.objects.filter(
                barbeiro=barbeiro,
                horario=horario,
                ativo=True,
            ).exists()
            if not horario_valido:
                raise ValidationError('Este horário não está disponível para o barbeiro selecionado.')

        return cleaned_data


class MensagemContatoForm(forms.ModelForm):
    class Meta:
        model = MensagemContato
        fields = ['nome', 'email', 'telefone', 'mensagem']
        labels = {
            'nome': 'Nome completo',
            'email': 'Endereço de e-mail',
            'telefone': 'Número de telefone',
            'mensagem': 'Mensagem ou dúvida',
        }
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'mensagem': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class AgendamentoPublicoForm(forms.Form):
    servico = forms.ModelChoiceField(
        queryset=Servico.objects.filter(ativo=True),
        label='Serviço Principal',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    barbeiro = forms.ModelChoiceField(
        queryset=Barbeiro.objects.filter(ativo=True),
        label='Barbeiro de Preferência',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    data = forms.DateField(
        label='Data do Atendimento',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    horario = forms.TimeField(
        label='Horário',
        widget=forms.HiddenInput(),
    )
    nome = forms.CharField(
        max_length=200,
        label='Nome Completo',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Seu nome'}),
    )
    telefone = forms.CharField(
        max_length=20,
        label='Telefone / WhatsApp',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(44) 99999-9999'}),
    )
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'seu@email.com'}),
    )
    observacoes = forms.CharField(
        required=False,
        label='Observações Especiais',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Preferências, estilo de barba, etc.'}),
    )

    def clean_data(self):
        data_agendamento = self.cleaned_data.get('data')
        if data_agendamento and data_agendamento < date.today():
            raise ValidationError('Não é possível agendar em datas passadas.')
        return data_agendamento

    def clean(self):
        cleaned_data = super().clean()
        barbeiro = cleaned_data.get('barbeiro')
        data_agendamento = cleaned_data.get('data')
        horario = cleaned_data.get('horario')

        if barbeiro and data_agendamento and horario:
            exists = Agendamento.objects.filter(
                barbeiro=barbeiro,
                data=data_agendamento,
                horario=horario,
            ).exclude(status=Agendamento.Status.CANCELADO).exists()
            if exists:
                raise ValidationError('Este horário já está reservado para o barbeiro selecionado.')

            horario_valido = HorarioDisponivel.objects.filter(
                barbeiro=barbeiro,
                horario=horario,
                ativo=True,
            ).exists()
            if not horario_valido:
                raise ValidationError('Este horário não está disponível para o barbeiro selecionado.')

        return cleaned_data


class CadastroForm(forms.Form):
    nome = forms.CharField(max_length=150, label='Nome', widget=forms.TextInput(attrs={'class': 'form-control'}))
    sobrenome = forms.CharField(max_length=150, label='Sobrenome', widget=forms.TextInput(attrs={'class': 'form-control'}))
    usuario = forms.CharField(max_length=150, label='Usuário', widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='E-mail', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    telefone = forms.CharField(max_length=20, label='Telefone / WhatsApp', widget=forms.TextInput(attrs={'class': 'form-control'}))
    senha = forms.CharField(label='Senha', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirmar_senha = forms.CharField(label='Confirmar Senha', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean_usuario(self):
        username = self.cleaned_data.get('usuario')
        if User.objects.filter(username=username).exists():
            raise ValidationError('Este nome de usuário já está em uso.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Este e-mail já está em uso.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get('senha')
        confirmar_senha = cleaned_data.get('confirmar_senha')
        if senha and confirmar_senha and senha != confirmar_senha:
            raise ValidationError('As senhas não coincidem.')
        return cleaned_data


class PerfilUpdateForm(forms.Form):
    nome = forms.CharField(max_length=150, label='Nome', widget=forms.TextInput(attrs={'class': 'form-control'}))
    sobrenome = forms.CharField(max_length=150, label='Sobrenome', widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='E-mail', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    telefone = forms.CharField(max_length=20, label='Telefone / WhatsApp', widget=forms.TextInput(attrs={'class': 'form-control'}))
    foto_perfil = forms.ImageField(label='Foto de Perfil', required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['nota', 'comentario']
        widgets = {
            'nota': forms.Select(attrs={'class': 'form-control'}),
            'comentario': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class FotoTrabalhoForm(forms.ModelForm):
    class Meta:
        model = FotoTrabalho
        fields = ['titulo', 'descricao', 'imagem', 'categoria', 'publicado']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'imagem': forms.FileInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'publicado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ==============================================================================
# NOVOS FORMULÁRIOS DE GESTÃO E SERVIÇOS
# ==============================================================================

class PlanoAssinaturaForm(forms.ModelForm):
    class Meta:
        model = PlanoAssinatura
        exclude = ['criado_em', 'atualizado_em']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'preco_mensal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quantidade_creditos': forms.NumberInput(attrs={'class': 'form-control'}),
            'servicos': forms.CheckboxSelectMultiple(),
            'desconto_produtos': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'validade_dias': forms.NumberInput(attrs={'class': 'form-control'}),
            'permite_acumular': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'destaque': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        exclude = ['criado_em', 'atualizado_em']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'categoria': forms.TextInput(attrs={'class': 'form-control'}),
            'custo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'preco': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'estoque_atual': forms.NumberInput(attrs={'class': 'form-control'}),
            'estoque_minimo': forms.NumberInput(attrs={'class': 'form-control'}),
            'unidade': forms.TextInput(attrs={'class': 'form-control'}),
            'imagem': forms.FileInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MovimentacaoEstoqueForm(forms.ModelForm):
    class Meta:
        model = MovimentacaoEstoque
        fields = ['produto', 'tipo', 'quantidade', 'motivo']
        widgets = {
            'produto': forms.Select(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control'}),
            'motivo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Compra NF 1234 / Reposição'}),
        }


class ItemComandaForm(forms.ModelForm):
    class Meta:
        model = ItemComanda
        fields = ['tipo', 'servico', 'produto', 'descricao', 'quantidade', 'preco_unitario']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control', 'id': 'id_item_tipo'}),
            'servico': forms.Select(attrs={'class': 'form-control'}),
            'produto': forms.Select(attrs={'class': 'form-control'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'value': 1}),
            'preco_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class RegraComissaoForm(forms.ModelForm):
    class Meta:
        model = RegraComissao
        fields = ['barbeiro', 'percentual_servico', 'percentual_produto', 'ativo']
        widgets = {
            'barbeiro': forms.Select(attrs={'class': 'form-control'}),
            'percentual_servico': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'percentual_produto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MetaBarbeiroForm(forms.ModelForm):
    class Meta:
        model = MetaBarbeiro
        fields = ['barbeiro', 'mes', 'ano', 'meta_faturamento', 'meta_atendimentos', 'meta_produtos']
        widgets = {
            'barbeiro': forms.Select(attrs={'class': 'form-control'}),
            'mes': forms.NumberInput(attrs={'class': 'form-control'}),
            'ano': forms.NumberInput(attrs={'class': 'form-control'}),
            'meta_faturamento': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'meta_atendimentos': forms.NumberInput(attrs={'class': 'form-control'}),
            'meta_produtos': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class RepasseComissaoForm(forms.ModelForm):
    class Meta:
        model = RepasseComissao
        fields = ['barbeiro', 'valor', 'periodo_inicio', 'periodo_fim', 'observacao']
        widgets = {
            'barbeiro': forms.Select(attrs={'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'periodo_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'periodo_fim': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ConfiguracaoEstabelecimentoForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoEstabelecimento
        fields = [
            'tipo_sinal', 'valor_sinal', 'minutos_expiracao_pix',
            'chave_pix', 'titular_pix', 'cidade_pix',
            'lembrete_horas_antes', 'cancelamento_antecedencia_horas'
        ]
        widgets = {
            'tipo_sinal': forms.Select(attrs={'class': 'form-control'}),
            'valor_sinal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'minutos_expiracao_pix': forms.NumberInput(attrs={'class': 'form-control'}),
            'chave_pix': forms.TextInput(attrs={'class': 'form-control'}),
            'titular_pix': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade_pix': forms.TextInput(attrs={'class': 'form-control'}),
            'lembrete_horas_antes': forms.NumberInput(attrs={'class': 'form-control'}),
            'cancelamento_antecedencia_horas': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ListaEsperaForm(forms.ModelForm):
    class Meta:
        model = ListaEspera
        fields = ['servico', 'barbeiro', 'data_desejada', 'horario_inicio', 'horario_fim']
        widgets = {
            'servico': forms.Select(attrs={'class': 'form-control'}),
            'barbeiro': forms.Select(attrs={'class': 'form-control'}),
            'data_desejada': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'horario_inicio': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'horario_fim': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }

    def clean_data_desejada(self):
        data_escolhida = self.cleaned_data.get('data_desejada')
        if data_escolhida and data_escolhida < date.today():
            raise ValidationError('A data desejada não pode ser no passado.')
        return data_escolhida


class AnaliseEstiloForm(forms.Form):
    imagem = forms.ImageField(
        label='Foto do seu Rosto',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        help_text='Tire uma foto frontal, com boa iluminação e rosto centralizado.'
    )
    consentimento = forms.BooleanField(
        label='Concordo com a análise biométrica e de visagismo da minha imagem.',
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class HistoricoVisualClienteForm(forms.ModelForm):
    class Meta:
        model = HistoricoVisualCliente
        fields = ['cliente', 'barbeiro', 'agendamento', 'imagem', 'consentimento', 'observacoes']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'barbeiro': forms.Select(attrs={'class': 'form-control'}),
            'agendamento': forms.Select(attrs={'class': 'form-control'}),
            'imagem': forms.FileInput(attrs={'class': 'form-control'}),
            'consentimento': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

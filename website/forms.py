from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from datetime import date
from .models import (
    Servico, Barbeiro, Cliente, HorarioDisponivel, Agendamento,
    MensagemContato, PerfilUsuario, Feedback, FotoTrabalho
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

        if barbeiro and data_agendamento and horario:
            # Check duplicate appointment (excluding the current one if updating)
            query = Agendamento.objects.filter(
                barbeiro=barbeiro,
                data=data_agendamento,
                horario=horario,
            ).exclude(status='Cancelado')

            if self.instance and self.instance.pk:
                query = query.exclude(pk=self.instance.pk)

            if query.exists():
                raise ValidationError('Este horário já está reservado para o barbeiro selecionado.')

            # Check if timeslot is valid for barber
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
        label='Serviço',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    barbeiro = forms.ModelChoiceField(
        queryset=Barbeiro.objects.filter(ativo=True),
        label='Barbeiro',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    data = forms.DateField(
        label='Data',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    horario = forms.TimeField(
        label='Horário',
        widget=forms.HiddenInput(),
    )
    nome = forms.CharField(
        max_length=200,
        label='Nome Completo',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    telefone = forms.CharField(
        max_length=20,
        label='Telefone / WhatsApp',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    observacoes = forms.CharField(
        required=False,
        label='Observações',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
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
            # Check if slot is already booked
            exists = Agendamento.objects.filter(
                barbeiro=barbeiro,
                data=data_agendamento,
                horario=horario,
            ).exclude(status='Cancelado').exists()
            if exists:
                raise ValidationError('Este horário já está reservado para o barbeiro selecionado.')

            # Check if timeslot is valid for barber
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


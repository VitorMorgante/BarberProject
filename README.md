# Delacruz Barber

Sistema web de agendamento para a barbearia Delacruz Barber, desenvolvido com Django.

## Sobre o Projeto
O **Delacruz Barber** é uma plataforma web premium desenvolvida para gerenciar agendamentos e o relacionamento com os clientes de uma barbearia de alto padrão. O sistema automatiza o fluxo de marcação de horários, substituindo processos manuais por uma solução online ágil, robusta e moderna.

## Para que está sendo desenvolvido?
Este projeto foi desenvolvido para atender às seguintes necessidades:
1. **Praticidade para o Cliente**: Agendamento online de forma rápida, onde o cliente escolhe o serviço, o barbeiro de sua preferência, além do dia e horário mais convenientes.
2. **Organização para os Profissionais**: Painéis e telas dedicadas para os barbeiros visualizarem e controlarem seus agendamentos diários, histórico de serviços realizados e controle de portfólio.
3. **Gestão Estratégica**: Um dashboard administrativo para acompanhar estatísticas do dia, fluxo de clientes, faturamento estimado e controle total do cadastro de serviços e profissionais.

## Quem são os Barbeiros?
A equipe da Delacruz Barber é composta por profissionais de elite:
- **Danilo Delacruz (Barbeiro Chefe)**: Fundador da barbearia. Especialista em cortes masculinos clássicos e modernos, cortes degradê e acabamento ultra preciso.
- **Heitor Pontes (Barbeiro)**: Especialista em cortes modernos de cabelo, design de barba alinhada e técnicas de finalização capilar.

## Tecnologias
- Python / Django
- Bootstrap 5
- Django Crispy Forms
- SQLite

## Instalação

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py seed
python manage.py createsuperuser
python manage.py runserver
```

## Páginas Públicas
- Início: http://127.0.0.1:8000/
- Serviços: http://127.0.0.1:8000/servicos/
- Barbeiros: http://127.0.0.1:8000/barbeiros/
- Sobre: http://127.0.0.1:8000/sobre/
- Contato: http://127.0.0.1:8000/contato/
- Agendamento: http://127.0.0.1:8000/agendamento/

## Área Administrativa
- Dashboard: http://127.0.0.1:8000/dashboard/
- Login: http://127.0.0.1:8000/login/

## Funcionalidades
- Agendamento online com seleção de serviço, barbeiro, data e horário
- Dashboard com estatísticas do dia
- CRUD completo para serviços, barbeiros, clientes, horários e agendamentos
- Formulário de contato com persistência no banco de dados
- Autenticação com login, logout e alteração de senha
- Filtragem de registros por usuário logado

## Autores
- Danilo Delacruz

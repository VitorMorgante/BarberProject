# Delacruz Barber

Sistema web de agendamento para a barbearia Delacruz Barber, desenvolvido com Django.

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

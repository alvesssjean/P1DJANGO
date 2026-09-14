# 🚀 Projeto Django - Guia de Instalação e Execução

Este projeto foi desenvolvido em Python/Django. Siga o passo a passo abaixo para configurar o ambiente localmente e testar a aplicação.

---

## 📋 Pré-requisitos

Certifique-se de ter instalado em sua máquina:
* **Python 3.10+**
* **Git**
* **pip** (Gerenciador de pacotes do Python)

---

## ⚙️ Passo a Passo para Execução

### 1. Clonar o Repositório
git clone <URL_DO_SEU_REPOSITORIO>
cd <NOME_DA_PASTA_DO_PROJETO>

### 2. Criar e Ativar o Ambiente Virtual (venv)

* **Linux / macOS:**
  python3 -m venv venv
  source venv/bin/activate

* **Windows (PowerShell / Prompt):**
  python -m venv venv
  .\venv\Scripts\activate

### 3. Instalar as Dependências
Com o ambiente virtual ativado, instale os pacotes requeridos:
pip install -r requirements.txt

---

## 🔑 Configuração das Variáveis de Ambiente (.env)

1. Faça uma cópia do arquivo .env.example e nomeie-a como .env:
   * **Linux/macOS:** cp .env.example .env
   * **Windows:** copy .env.example .env

2. O arquivo .env gerado já contém credenciais padrão para avaliação:

   SECRET_KEY=sua_secret_key_aqui
   DEBUG=True

   # Credenciais do Superusuário para testes
   DJANGO_SUPERUSER_USERNAME=admin
   DJANGO_SUPERUSER_EMAIL=admin@exemplo.com
   DJANGO_SUPERUSER_PASSWORD=admin123

*(Caso deseje, altere os valores diretamente no arquivo .env).*

---

## 🗄️ Banco de Dados e Criação de Superusuário

### 1. Executar as Migrações
Execute os comandos abaixo para estruturar o banco de dados local (SQLite):
python manage.py makemigrations
python manage.py migrate

### 2. Criar o Superusuário Automaticamente
Para criar o usuário administrador com as credenciais definidas no arquivo .env, execute:
python manage.py createsuperuser --noinput

> 🔑 Credenciais padrão geradas:
> * Usuário: admin
> * Senha: admin123

---

## 🚀 Executando o Servidor Local

Inicie o servidor de desenvolvimento:
python manage.py runserver

Acesse no seu navegador:
* Aplicação Principal: http://127.0.0.1:8000/
* Painel Administrativo: http://127.0.0.1:8000/admin/
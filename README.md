# 🚀 P1DJANGO — Sistema de Gestão de Tarefas (MVP)

Projeto desenvolvido em **Python/Django** para a entrega da fase **P1 (MVP Funcional)** da avaliação. O sistema permite o gerenciamento de projetos, tarefas, subtarefas e dependências entre tarefas, com controle de acesso por usuário.

## 📌 Funcionalidades (P1)

- **Cadastro e autenticação de usuários**, com criação automática de um `Membro` vinculado ao `User` do Django.
- **Gestão de Projetos**, associados a um membro responsável (`dono`).
- **Gestão de Tarefas**, vinculadas opcionalmente a um projeto e sempre a um usuário.
- **Subtarefas**, vinculadas a uma tarefa principal.
- **Dependências entre tarefas**: uma tarefa pode depender da conclusão de outra.
- **Regra de bloqueio de conclusão**: o sistema impede que uma tarefa seja marcada como concluída enquanto houver dependências pendentes (tarefas das quais ela depende ainda não concluídas). A validação ocorre na camada de modelo (`full_clean()` no `save()`), garantindo consistência mesmo fora das views.

### Entidades do sistema

| Entidade | Relacionamento |
|---|---|
| `Membro` | 1–1 com `User` (auth do Django) |
| `Projeto` | Pertence a um `Membro` (dono) |
| `Tarefa` | Pertence a um `User` e, opcionalmente, a um `Projeto` |
| `Subtarefa` | Pertence a uma `Tarefa` |
| `Dependência` | Relaciona uma `Tarefa` a outra `Tarefa` da qual ela depende |

---

## 📋 Pré-requisitos

Certifique-se de ter instalado em sua máquina:

- **Python 3.10+**
- **Git**
- **pip** (gerenciador de pacotes do Python)

---

## ⚙️ Guia de Instalação e Execução

### 1. Clonar o repositório

```bash
git clone https://github.com/alvesssjean/P1DJANGO.git
cd P1DJANGO
```

### 2. Criar e ativar o ambiente virtual (venv)

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell / Prompt):**
```bash
python -m venv venv
.\venv\Scripts\activate
```

### 3. Instalar as dependências

Com o ambiente virtual ativado:
```bash
pip install -r requirements.txt
```

---

## 🔑 Configuração das Variáveis de Ambiente (.env)

1. Faça uma cópia do arquivo `.env.example` e nomeie-a como `.env`:

**Linux / macOS:**
```bash
cp .env.example .env
```

**Windows:**
```bash
copy .env.example .env
```

2. O arquivo `.env` gerado já contém valores padrão para avaliação:

```env
SECRET_KEY=sua_secret_key_aqui
DEBUG=True

# Credenciais do Superusuário para testes
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@exemplo.com
DJANGO_SUPERUSER_PASSWORD=admin123
```

*(Altere os valores diretamente no arquivo `.env`, se desejar.)*

---

## 🗄️ Banco de Dados e Criação do Superusuário

### 1. Executar as migrações

```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Criar o superusuário automaticamente

Usando as credenciais definidas no `.env`:

```bash
python manage.py createsuperuser --noinput
```

> 🔑 **Credenciais padrão geradas:**
> - Usuário: `admin`
> - Senha: `admin123`

---

## 🚀 Executando o Servidor Local

```bash
python manage.py runserver
```

Acesse no navegador:

- **Aplicação principal:** http://127.0.0.1:8000/
- **Painel administrativo:** http://127.0.0.1:8000/admin/

---

## 🧪 Testando a Regra de Bloqueio por Dependência

1. Acesse `/admin/` com as credenciais do superusuário.
2. Crie duas tarefas (ex: "Tarefa A" e "Tarefa B").
3. Cadastre uma `Dependência` informando que "Tarefa B" depende de "Tarefa A".
4. Tente concluir "Tarefa B" antes de concluir "Tarefa A" — o sistema deve impedir a conclusão e exibir uma mensagem de erro.
5. Conclua "Tarefa A" e tente novamente concluir "Tarefa B" — agora a conclusão deve ser permitida.
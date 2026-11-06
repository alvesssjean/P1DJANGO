# Melhorias da P1

## 1. Configurações inseguras em `settings.py`
- **Problema:** `SECRET_KEY` está escrita no código, `DEBUG = True` e `ALLOWED_HOSTS = []`. O `.env` é carregado, mas só para as variáveis de superuser.
- **Correção:** mover `SECRET_KEY` e `DEBUG` para o `.env`, definir `ALLOWED_HOSTS` e confirmar que `.env` está no `.gitignore`.

## 2. Views `concluir_tarefa` e `deletar_tarefa` sem resposta para GET
- **Problema:** as duas views só tratam `POST`. Em uma requisição `GET`, retornam `None`, o que gera erro 500. Em `concluir_tarefa`, o `ValidationError` é exibido, mas a tarefa continua marcada como concluída em memória.
- **Correção:** retornar `redirect('home')` ao final de cada view (ou usar `@require_POST`) e reverter `tarefa.concluida` quando a validação falhar.

## 3. Regras de negócio espalhadas
- **Problema:** a regra de ciclo de dependências está em `DependenciaForm.clean()`, enquanto a de conclusão está em `Tarefa.clean()`. Assim, a API (P2) não herdará a validação de ciclo.
- **Correção:** mover a verificação de ciclo para `Dependencia.clean()` do model e manter o form apenas chamando o model.

## 4. Modelagem de propriedade duplicada
- **Problema:** `Tarefa` tem `user` (FK para `User`), e `Projeto` tem `dono` (FK para `Membro`). Há dois conceitos de dono. Além disso, `Tarefa.user` e `Projeto.dono` podem apontar para pessoas diferentes.
- **Correção:** deixar apenas um vínculo de responsabilidade, ou documentar a diferença entre "criador" e "responsável". Esse ponto também prepara a P2 (multi-organização).

## 5. Código e configuração inconsistentes
- **Problema:** `views.py` tem `tecnologias` hardcoded no contexto e `HttpResponse` importado sem uso. O `requirements.txt` parece estar em UTF-16 (cada letra aparece separada por espaço), e o `settings.py` foi gerado pelo Django 5.2.15, enquanto o `requirements.txt` lista Django 6.1.2.
- **Correção:** remover o código morto, salvar o `requirements.txt` em UTF-8 com `pip freeze > requirements.txt` e alinhar as versões.

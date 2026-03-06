# Manuals.md — Руководство пользователя и разработчика

## Содержание

1. [Настройка Bitrix24](#1-настройка-bitrix24)
2. [Аутентификация](#2-аутентификация)
3. [Shell CLI](#3-shell-cli-bx24)
4. [Python API — Ядро](#4-python-api--ядро)
5. [Бандл: Kanban](#5-бандл-kanban)
6. [Бандл: Смарт-процессы](#6-бандл-смарт-процессы)
7. [Бизнес-процессы](#7-бизнес-процессы)
8. [Phase 2: Quarkus Stand](#8-phase-2-quarkus-stand)
9. [Bridge API Reference](#9-bridge-api-reference)
10. [Примеры use-case](#10-примеры-use-case)

---

## 1. Настройка Bitrix24

### Создание входящего webhook (рекомендуется для разработки)

1. Откройте Bitrix24 → **Приложения** → **Вебхуки** → **Входящий вебхук**
2. Укажите название, выберите пользователя
3. Назначьте необходимые права (tasks, crm, bizproc и т.д.)
4. Скопируйте URL вида:
   `https://your-portal.bitrix24.com/rest/1/abc123def456/`
5. Установите переменные окружения:
   ```bash
   export BX24_DOMAIN="your-portal.bitrix24.com"
   export BX24_USER_ID=1
   export BX24_WEBHOOK_TOKEN="abc123def456"
   ```

### Создание OAuth2 приложения (для production)

1. Bitrix24 → **Разработчикам** → **Другое** → **Приложение**
2. Тип: Локальное приложение
3. Права: tasks, crm, bizproc, user
4. Скопируйте CLIENT_ID и CLIENT_SECRET

---

## 2. Аутентификация

### Webhook

```python
from core.auth import WebhookAuth

auth = WebhookAuth(
    domain="your-portal.bitrix24.com",
    user_id=1,
    token="your_webhook_token"
)
```

### OAuth2

```python
from core.auth import OAuth2Auth

auth = OAuth2Auth(
    domain="your-portal.bitrix24.com",
    client_id="...",
    client_secret="...",
    access_token="...",     # Получается через OAuth2 flow
    refresh_token="...",    # Автоматически обновляется
)
```

---

## 3. Shell CLI (`bx24`)

### Синтаксис

```
python cli/main.py [--verbose] [--format pretty|json|raw] <команда> [параметры]
```

### Команды

#### Прямой вызов API

```bash
# Вызов любого метода Bitrix24
python cli/main.py call <method> [--param KEY=VALUE ...]

# Примеры:
python cli/main.py call user.current
python cli/main.py call user.get --param ID=1
python cli/main.py call crm.deal.list --param "filter[STAGE_ID]=WON"
python cli/main.py call task.item.add --param "fields[TITLE]=Задача" --param "fields[RESPONSIBLE_ID]=1"
```

#### Пользователи

```bash
python cli/main.py user list [--filter KEY=VALUE ...]
python cli/main.py user get --id <user_id>
python cli/main.py user current
```

#### Задачи

```bash
python cli/main.py task list [--filter KEY=VALUE ...]
python cli/main.py task get --id <task_id>
python cli/main.py task add --title "..." [--responsible <id>] [--deadline YYYY-MM-DD] [--field KEY=VALUE ...]
python cli/main.py task update --id <task_id> [--field KEY=VALUE ...]
python cli/main.py task delete --id <task_id>
python cli/main.py task stages [--entity-type 1|2]
```

#### CRM (сделки)

```bash
python cli/main.py crm deal list [--filter KEY=VALUE ...]
python cli/main.py crm deal get --id <deal_id>
python cli/main.py crm deal add --title "..." [--stage STAGE_ID] [--field KEY=VALUE ...]
python cli/main.py crm deal update --id <deal_id> [--field KEY=VALUE ...]
python cli/main.py crm deal delete --id <deal_id>
```

#### Смарт-процессы

```bash
# Типы
python cli/main.py smart type-list
python cli/main.py smart type-add --title "Service Requests" [--field KEY=VALUE ...]

# Элементы
python cli/main.py smart list --type-id <entityTypeId> [--filter KEY=VALUE ...]
python cli/main.py smart add --type-id <entityTypeId> --title "..." [--field KEY=VALUE ...]
python cli/main.py smart get --type-id <entityTypeId> --id <item_id>
python cli/main.py smart update --type-id <entityTypeId> --id <item_id> [--field KEY=VALUE ...]
python cli/main.py smart delete --type-id <entityTypeId> --id <item_id>

# Этапы пайплайна
python cli/main.py smart stages --type-id <entityTypeId>
```

#### Бизнес-процессы

```bash
python cli/main.py bp list
python cli/main.py bp templates
python cli/main.py bp tasks [--workflow-id <id>]
python cli/main.py bp start --template-id <id> --document MODULE:ENTITY:ID [--param KEY=VALUE ...]
python cli/main.py bp terminate --workflow-id <id>
python cli/main.py bp kill --workflow-id <id>
```

#### Батч-запросы

```bash
python cli/main.py batch --cmd "KEY:method?param=value" [--cmd ...]
# Пример:
python cli/main.py batch \
  --cmd "user:user.get?ID=1" \
  --cmd "tasks:task.item.list" \
  --cmd "deals:crm.deal.list"
```

#### Формат вывода

```bash
python cli/main.py --format json user list    # JSON
python cli/main.py --format pretty user list  # Форматированный (по умолчанию)
python cli/main.py --format raw user list     # Сырой вывод
```

---

## 4. Python API — Ядро

### Bitrix24Client

```python
from core import Bitrix24Client, WebhookAuth

client = Bitrix24Client.from_env()  # Из переменных окружения

# Одиночный вызов
result = client.call("user.current")

# Получить все записи (автопагинация)
all_tasks = client.get_all("task.item.list", {
    "ORDER": {"ID": "DESC"},
    "FILTER": {"RESPONSIBLE_ID": 1},
})

# Итератор (экономит память)
for task in client.iter_all("task.item.list"):
    print(task["TITLE"])

# Батч-запрос
results = client.get_batch({
    "user": "user.get?ID=1",
    "deals": "crm.deal.list",
})
```

### Методы API

```python
from core.methods import (
    UserMethods, TaskMethods, CRMMethods,
    SmartProcessMethods, BusinessProcessMethods
)

# Пользователи
users = UserMethods(client)
me = users.current()
user = users.get(1)
all_users = users.list(filter={"ACTIVE": "Y"})

# Задачи
tasks = TaskMethods(client)
tid = tasks.add({"TITLE": "Задача", "RESPONSIBLE_ID": 1})
task = tasks.get(tid)
tasks.update(tid, {"STATUS": "5"})  # 5 = Done
tasks.delete(tid)
stages = tasks.get_stages(entity_type=1)
tasks.move_to_stage(tid, stage_id=5)

# CRM
crm = CRMMethods(client)
deal_id = crm.deal_add({"TITLE": "Сделка", "STAGE_ID": "NEW"})
deal = crm.deal_get(deal_id)
crm.deal_update(deal_id, {"STAGE_ID": "WON"})

# Смарт-процессы
sp = SmartProcessMethods(client)
types = sp.type_list()
new_type = sp.type_add({"title": "IT Requests", "isStagesEnabled": True})
item = sp.item_add(128, {"title": "Запрос #1", "stageId": "DT128_1:NEW"})
items = sp.item_list(128, filter={"stageId": "DT128_1:NEW"})

# Бизнес-процессы
bp = BusinessProcessMethods(client)
workflows = bp.workflow_list()
wf_id = bp.workflow_start(template_id=5, document_id=["crm", "CCrmLead", "1"])
bp.workflow_terminate(wf_id)
```

---

## 5. Бандл: Kanban

### Использование

```python
from bundles.kanban import KanbanBoard
from core import Bitrix24Client, WebhookAuth

client = Bitrix24Client.from_env()
board = KanbanBoard(client, entity_type=1)  # 1=Мои задачи, 2=Группа

# Получить состояние доски
state = board.get_board_state()
print(f"Всего карточек: {state.total_cards}")
for stage in state.stages:
    print(f"  [{stage.title}]: {stage.task_count} задач")

# Создать этап
new_stage = board.add_stage("In Review", color="#ff9900", sort=30)

# Создать карточку
card = board.add_card(
    title="Новая задача",
    stage_id=new_stage.id,
    responsible_id=1,
    deadline="2026-12-31",
    tags=["urgent", "bug"],
)

# Переместить карточку
board.move_card(task_id=card.id, to_stage_id=5)

# Статус живучести (для витрины)
health = board.get_health_status()
print(health)  # {"bundle": "kanban", "status": "healthy", ...}
```

---

## 6. Бандл: Смарт-процессы

### Use-case: Service Desk компании

```python
from bundles.smart_processes import SmartProcess, Pipeline

sp = SmartProcess(client)

# 1. Создание типа "Service Requests"
svc_type = sp.create_type(
    title="Service Requests",
    code="SERVICE_REQ",
    use_kanban=True,
    use_bp=True,
)
print(f"Тип создан: entityTypeId={svc_type.entity_type_id}")

# 2. Инициализация пайплайна
pipeline = Pipeline(client, entity_type_id=svc_type.entity_type_id)
stages = pipeline.initialize_default_pipeline()
# Создаёт: New -> In Progress -> In Review -> Done -> Cancelled

# 3. Создание заявок
requests = [
    "Починить принтер в офисе 301",
    "Настроить ноутбук нового сотрудника",
    "Восстановить доступ к корпоративной почте",
    "Установить VPN-клиент",
]
items = []
for title in requests:
    item = sp.add_item(
        entity_type_id=svc_type.entity_type_id,
        title=title,
        stage_id=stages[0].semantic_id or str(stages[0].id),
        assigned_by_id=1,
    )
    items.append(item)
    print(f"  Создана заявка #{item.id}: {title}")

# 4. Переход заявки в работу
sp.move_item_to_stage(
    item_id=items[0].id,
    entity_type_id=svc_type.entity_type_id,
    stage_id=stages[1].semantic_id or str(stages[1].id),
)

# 5. Просмотр состояния процесса
state = sp.get_process_state(svc_type.entity_type_id)
for stage in state["stages"]:
    print(f"  {stage['title']}: {stage['item_count']} заявок")

# 6. Получение всех заявок в стадии "New"
new_items = sp.list_items(
    entity_type_id=svc_type.entity_type_id,
    stage_id=stages[0].semantic_id,
)
```

### Управление бизнес-процессами

```python
# Запуск бизнес-процесса уведомлений для заявки
wf_id = sp.start_workflow(
    item_id=items[0].id,
    entity_type_id=svc_type.entity_type_id,
    template_id=5,  # ID шаблона BP
    parameters={"NotifyTo": "manager@company.com"},
)

# Пауза выполнения
sp.pause_workflow(wf_id)

# Продолжение (через start нового или through bizproc.task.complete)
# sp.stop_workflow(wf_id)    # Полная остановка

# Принудительное удаление
sp.delete_workflow(wf_id)

# Список всех запущенных BP
all_wf = sp.list_workflows()
```

---

## 7. Бизнес-процессы

### Прямое управление через API

```python
from core.methods import BusinessProcessMethods

bp = BusinessProcessMethods(client)

# Список шаблонов
templates = bp.template_list()

# Запуск BP для CRM Lead
wf_id = bp.workflow_start(
    template_id=5,
    document_id=["crm", "CCrmLead", "1"],
    parameters={"priority": "high"},
)

# Список запущенных экземпляров
instances = bp.workflow_list()

# Задачи BP, ожидающие выполнения
tasks = bp.task_list(workflow_id=wf_id)

# Завершение задачи BP
bp.task_complete(
    task_id=tasks[0]["ID"],
    status="Y",  # Y = одобрено
    comment="Согласовано руководством",
)

# Остановка BP
bp.workflow_terminate(wf_id)
```

---

## 8. Phase 2: Quarkus Stand

### Запуск

```bash
# 1. Запустить Python bridge
export BX24_DOMAIN=...
export BX24_WEBHOOK_TOKEN=...
python bridge/server.py
# Bridge запущен на http://localhost:5000

# 2. Запустить Quarkus
cd quarkus-stand
mvn quarkus:dev
# Stand запущен на http://localhost:8080
# Swagger UI: http://localhost:8080/swagger-ui
```

### REST API Quarkus Stand

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/vitrine` | Полное состояние витрины |
| GET | `/vitrine/bundles` | Список бандлов со статусами |
| GET | `/vitrine/bundles/{name}` | Статус конкретного бандла |
| GET | `/kanban/{entityType}/board` | Состояние Kanban-доски |
| POST | `/kanban/{entityType}/cards/{id}/move` | Переместить карточку |
| GET | `/smart/types` | Список смарт-процессов |
| GET | `/smart/{entityTypeId}/state` | Состояние смарт-процесса |
| POST | `/smart/{entityTypeId}/items` | Создать элемент |
| POST | `/smart/{entityTypeId}/items/{id}/move` | Переместить элемент |
| GET | `/bp/workflows` | Список BP workflow |
| POST | `/bp/workflows` | Запустить workflow |
| POST | `/bp/workflows/{id}/pause` | Пауза workflow |
| POST | `/bp/workflows/{id}/stop` | Остановить workflow |
| DELETE | `/bp/workflows/{id}` | Удалить workflow |
| GET | `/health` | Общий health-check |
| GET | `/health/ready` | Readiness (проверяет bridge) |

---

## 9. Bridge API Reference

Bridge-сервер (`bridge/server.py`) доступен на `http://localhost:5000`.

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v1/health` | Статус bridge |
| GET | `/api/v1/bundles/status` | Статусы всех бандлов |
| GET | `/api/v1/kanban/{type}/board` | Kanban-доска |
| POST | `/api/v1/kanban/{type}/cards/{id}/move?stage_id=N` | Переместить карточку |
| GET | `/api/v1/smart/types` | Типы смарт-процессов |
| GET | `/api/v1/smart/{typeId}/state` | Состояние смарт-процесса |
| POST | `/api/v1/smart/{typeId}/items` | Создать элемент |
| POST | `/api/v1/smart/{typeId}/items/{id}/move?stage_id=S` | Переместить элемент |
| GET | `/api/v1/bp/workflows` | Список workflow |
| POST | `/api/v1/bp/workflows/start` | Запустить workflow |
| POST | `/api/v1/bp/workflows/{id}/pause` | Пауза |
| POST | `/api/v1/bp/workflows/{id}/stop` | Остановить |
| DELETE | `/api/v1/bp/workflows/{id}` | Удалить |

---

## 10. Примеры use-case

### Use-case 1: Отдел IT-поддержки

**Сценарий**: Компания ведёт заявки на IT-поддержку через смарт-процесс.
Сотрудники создают заявки, IT-специалисты принимают их в работу и закрывают.

**Пайплайн**:
```
Новая → В работе → На проверке → Выполнена
                                  ↘ Отклонена
```

**Автоматизация через BP**:
- При создании заявки → уведомление в Slack/почту IT-отделу
- При переходе "В работе" → уведомление заявителю
- При "Выполнена" → запрос оценки заявителю

### Use-case 2: Kanban для разработки

**Сценарий**: Команда разработки управляет задачами через Kanban.

**Колонки**:
```
Backlog → In Progress → Code Review → Testing → Done
```

**CLI-команды**:
```bash
# Создать задачи в Backlog
python cli/main.py task add --title "Разработать API endpoint" --responsible 2
python cli/main.py task add --title "Написать unit-тесты" --responsible 3

# Просмотреть этапы
python cli/main.py task stages

# Перевести задачу в работу (через прямой вызов)
python cli/main.py call task.stages.movetask --param id=42 --param stageId=5
```

### Use-case 3: Операционные бизнес-процессы

**Сценарий**: Цепочка согласования заявки на отпуск.

```
Сотрудник создаёт заявку → Руководитель одобряет → HR обрабатывает → Заявка закрыта
```

```python
# Запуск цепочки согласования
wf_id = sp.start_workflow(
    item_id=request_item.id,
    entity_type_id=VACATION_TYPE_ID,
    template_id=APPROVAL_TEMPLATE_ID,
    parameters={
        "ApproverID": manager_id,
        "HRManagerID": hr_id,
    }
)

# Если нужна пауза (например, ожидание документов)
sp.pause_workflow(wf_id)

# Возобновление через завершение задачи BP
bp.task_complete(task_id, status="Y", comment="Документы получены")

# Если заявка отозвана — остановить процесс
sp.stop_workflow(wf_id)
```

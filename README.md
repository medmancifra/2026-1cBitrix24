# 2026-1cBitrix24 — Отладочный стенд / Debug Stand

Boilerplate проект для интеграции с **Bitrix24 REST API**.
Включает ядро (core), CLI-интерфейс командной строки, mini-app бандлы и микросервис визуализации на Kotlin Quarkus HeroUI.

---

## Структура проекта

```
2026-1cBitrix24/
├── core/                    # Ядро: REST-клиент, аутентификация, методы API
│   ├── __init__.py
│   ├── auth.py              # WebhookAuth, OAuth2Auth
│   ├── client.py            # Bitrix24Client (вызовы, пагинация, батч)
│   ├── methods.py           # UserMethods, TaskMethods, CRMMethods,
│   │                        #   SmartProcessMethods, BusinessProcessMethods
│   └── exceptions.py        # APIError, AuthError, RateLimitError, ...
│
├── cli/                     # Командная строка (shell)
│   └── main.py              # bx24 — CLI для всех методов Bitrix24 REST API
│
├── bundles/                 # Бандлы (mini-app)
│   ├── kanban/              # Kanban-доска (задачи)
│   │   ├── board.py         # KanbanBoard: управление этапами и карточками
│   │   └── models.py        # KanbanStage, KanbanCard, BoardState
│   └── smart_processes/     # Смарт-процессы (без CRM)
│       ├── process.py       # SmartProcess: полный жизненный цикл
│       ├── pipeline.py      # Pipeline: управление этапами пайплайна
│       └── models.py        # SmartProcessType, SmartItem, PipelineStage
│
├── bridge/                  # HTTP-мост Python -> Quarkus
│   └── server.py            # REST API-сервер (bridge) для Quarkus стенда
│
├── quarkus-stand/           # Phase 2: Kotlin Quarkus HeroUI микросервис
│   ├── pom.xml              # Maven (Quarkus 3.x, Kotlin 2.x)
│   └── src/main/kotlin/...  # REST-ресурсы, сервисы, health-чеки
│
├── tests/                   # Unit-тесты (62 теста, без HTTP-запросов)
│
├── README.md                # Этот файл
├── Roadmap.md               # Дорожная карта проекта
├── Testing.md               # Руководство по тестированию
└── Manuals.md               # Руководство пользователя и разработчика
```

---

## Быстрый старт

### 1. Требования

- Python 3.10+
- Bitrix24 портал (Cloud или On-premise)
- Для Phase 2: Java 21+, Maven 3.9+

### 2. Конфигурация (переменные окружения)

```bash
# Webhook (самый простой способ):
export BX24_DOMAIN="your-portal.bitrix24.com"
export BX24_USER_ID=1
export BX24_WEBHOOK_TOKEN="your_webhook_token"

# OAuth2 (для приложений):
export BX24_DOMAIN="your-portal.bitrix24.com"
export BX24_CLIENT_ID="your_client_id"
export BX24_CLIENT_SECRET="your_client_secret"
export BX24_ACCESS_TOKEN="your_access_token"
export BX24_REFRESH_TOKEN="your_refresh_token"
```

### 3. CLI — командная строка

```bash
# Прямой вызов любого метода
python cli/main.py call user.current

# Пользователи
python cli/main.py user list
python cli/main.py user get --id 1

# Задачи
python cli/main.py task list
python cli/main.py task add --title "Исправить баг" --responsible 1
python cli/main.py task stages

# CRM сделки
python cli/main.py crm deal list
python cli/main.py crm deal add --title "Крупная сделка" --stage NEW

# Смарт-процессы
python cli/main.py smart type-list
python cli/main.py smart list --type-id 128
python cli/main.py smart add --type-id 128 --title "Новый запрос"
python cli/main.py smart stages --type-id 128

# Бизнес-процессы
python cli/main.py bp list
python cli/main.py bp start --template-id 5 --document crm:CCrmLead:1
python cli/main.py bp terminate --workflow-id abc123

# Батч-запрос
python cli/main.py batch --cmd "u:user.get?ID=1" --cmd "d:crm.deal.list"

# Конфигурация
python cli/main.py config show
```

### 4. Python API (ядро)

```python
from core import Bitrix24Client, WebhookAuth
from core.methods import TaskMethods, SmartProcessMethods
from bundles.kanban import KanbanBoard
from bundles.smart_processes import SmartProcess

# Клиент
client = Bitrix24Client(auth=WebhookAuth(
    domain="your-portal.bitrix24.com",
    user_id=1,
    token="your_webhook_token",
))

# Задачи
tasks = TaskMethods(client)
task_id = tasks.add({"TITLE": "Тест", "RESPONSIBLE_ID": 1})
tasks.update(task_id, {"STATUS": "4"})

# Kanban-доска
board = KanbanBoard(client, entity_type=1)
state = board.get_board_state()
print(state.to_dict())

# Смарт-процесс
sp = SmartProcess(client)
svc_type = sp.create_type("Service Requests", code="SVC")
item = sp.add_item(svc_type.entity_type_id, "Починить принтер")
sp.move_item_to_stage(item.id, svc_type.entity_type_id, "NEW_STAGE_ID")
wf_id = sp.start_workflow(item.id, svc_type.entity_type_id, template_id=5)
sp.pause_workflow(wf_id)
sp.stop_workflow(wf_id)
sp.delete_workflow(wf_id)
```

### 5. Запуск тестов

```bash
python -m unittest discover -s tests -v
```

### 6. Bridge-сервер (Phase 2)

```bash
python bridge/server.py
# Сервер запускается на http://0.0.0.0:5000
```

### 7. Quarkus стенд (Phase 2)

```bash
cd quarkus-stand
mvn quarkus:dev
# Swagger UI: http://localhost:8080/swagger-ui
# Health: http://localhost:8080/health
```

---

## Этапы разработки

Смотри [Roadmap.md](Roadmap.md).

## Тестирование

Смотри [Testing.md](Testing.md).

## Руководство пользователя

Смотри [Manuals.md](Manuals.md).

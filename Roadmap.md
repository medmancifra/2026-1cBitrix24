# Roadmap — 2026-1cBitrix24 Отладочный стенд

## Обзор

Проект реализован в 3 этапа согласно техническому заданию.

---

## Этап 1 — Boilerplate Bitrix24 (Ядро + CLI + Бандлы)

**Статус: ЗАВЕРШЁН**

### Ядро (core/)

- [x] `WebhookAuth` — аутентификация через входящий webhook (постоянный токен)
- [x] `OAuth2Auth` — аутентификация через OAuth2 с автообновлением токена
- [x] `Bitrix24Client` — унифицированный REST-клиент
  - [x] `call()` — вызов одного метода
  - [x] `get_all()` — автопагинация (все страницы)
  - [x] `get_batch()` — пакетные запросы (до 50 команд за раз)
  - [x] `iter_all()` — итератор для больших наборов данных
  - [x] Retry-логика при rate limit (429)
  - [x] Преобразование вложенных параметров (fields[TITLE]=...)
- [x] `UserMethods` — user.get, user.current, user.search
- [x] `TaskMethods` — task.item.add/get/update/delete/list, task.stages.*
- [x] `CRMMethods` — crm.deal.*/crm.contact.list
- [x] `SmartProcessMethods` — crm.type.*, crm.item.*
- [x] `BusinessProcessMethods` — bizproc.workflow.*, bizproc.task.*
- [x] Кастомные исключения: `APIError`, `AuthError`, `RateLimitError`, `NotFoundError`

### CLI (cli/main.py)

- [x] `bx24 call <method>` — прямой вызов любого REST-метода
- [x] `bx24 user list/get/current`
- [x] `bx24 task list/get/add/update/delete/stages`
- [x] `bx24 crm deal list/get/add/update/delete`
- [x] `bx24 smart type-list/type-add/list/add/get/update/delete/stages`
- [x] `bx24 bp list/start/terminate/kill/templates/tasks`
- [x] `bx24 batch` — пакетный запрос
- [x] `bx24 config show`
- [x] Форматы вывода: pretty, json, raw

### Бандл: Kanban (bundles/kanban/)

- [x] `KanbanBoard` — управление доской задач
  - [x] `get_stages()` — список колонок
  - [x] `add_stage()` — создание колонки
  - [x] `update_stage()` — обновление
  - [x] `delete_stage()` — удаление
  - [x] `get_cards()` — карточки с фильтрацией
  - [x] `add_card()` — создание карточки
  - [x] `move_card()` — перемещение между колонками
  - [x] `get_board_state()` — полное состояние доски
  - [x] `get_health_status()` — статус живучести для витрины

### Бандл: Smart Processes (bundles/smart_processes/)

- [x] `SmartProcess` — полный жизненный цикл смарт-процесса
  - [x] `create_type()` / `list_types()` / `get_type()` / `delete_type()`
  - [x] `add_item()` / `get_item()` / `update_item()` / `delete_item()` / `list_items()`
  - [x] `move_item_to_stage()` — переход по этапам
  - [x] `start_workflow()` — запуск бизнес-процесса
  - [x] `pause_workflow()` — пауза (остановка-пауза)
  - [x] `stop_workflow()` — остановка
  - [x] `delete_workflow()` — удаление
  - [x] `get_process_state()` — состояние процесса для витрины
  - [x] `get_health_status()` — статус живучести
- [x] `Pipeline` — управление этапами пайплайна
  - [x] `get_stages()` / `add_stage()` / `update_stage()` / `delete_stage()`
  - [x] `initialize_default_pipeline()` — инициализация стандартного пайплайна

---

## Этап 2 — Подключение к Quarkus HeroUI стенду

**Статус: SCAFFOLD ГОТОВ** (ветка `dev-quarkus`)

> Микросервис визуализации на Kotlin Quarkus HeroUI.
> Визуальные экраны для проверки функционала бандлов.

### Архитектура

```
[Quarkus Stand :8080] <--REST--> [Python Bridge :5000] <--REST--> [Bitrix24 API]
```

### Выполнено

- [x] Maven проект с Quarkus 3.17, Kotlin 2.0, Java 21
- [x] `VitrineResource` — витрина бандлов (GET /vitrine, /vitrine/bundles)
- [x] `KanbanResource` — Kanban-экран (GET /kanban/{type}/board, POST move)
- [x] `SmartProcessResource` — Смарт-процессы (GET /smart/types, POST items)
- [x] `BusinessProcessResource` — БП (GET/POST/DELETE /bp/workflows)
- [x] `Bitrix24BridgeClient` — REST-клиент к Python bridge
- [x] MicroProfile Health check (`/health/ready`)
- [x] OpenAPI / Swagger UI (`/swagger-ui`)
- [x] Python Bridge server (`bridge/server.py`)

### Следующие шаги (Phase 2)

- [ ] Фронтенд HeroUI (React/Next.js компоненты для визуальных экранов)
- [ ] Авторизация (JWT/OAuth2 для Quarkus)
- [ ] Docker Compose для запуска всего стека
- [ ] WebSocket нотификации для real-time обновлений

---

## Этап 3 — Тестирование

**Статус: Unit-тесты готовы, интеграционные тесты — в плане**

### Выполнено

- [x] 62 unit-теста без реальных HTTP-запросов
  - [x] `test_auth.py` — 16 тестов (WebhookAuth, OAuth2Auth)
  - [x] `test_client.py` — 13 тестов (Bitrix24Client, flatten, batch)
  - [x] `test_kanban.py` — 18 тестов (KanbanBoard, models)
  - [x] `test_smart_processes.py` — 15 тестов (SmartProcess, Pipeline)

### Следующие шаги (Phase 3)

- [ ] Интеграционные тесты с реальным Bitrix24 порталом
- [ ] Тесты Quarkus микросервиса (`@QuarkusTest`)
- [ ] End-to-end тест: Quarkus → Bridge → Bitrix24 API
- [ ] Нагрузочное тестирование (rate limit, пагинация)

---

## Документация

- [x] README.md — быстрый старт
- [x] Roadmap.md — дорожная карта (этот файл)
- [x] Testing.md — руководство по тестированию
- [x] Manuals.md — руководство пользователя и разработчика

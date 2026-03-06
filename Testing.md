# Testing.md — Руководство по тестированию

## Обзор

Проект имеет многоуровневую стратегию тестирования:

1. **Unit-тесты** (Python) — быстрые тесты с моками, без реального API
2. **Интеграционные тесты** (Python) — тесты с реальным Bitrix24 порталом
3. **Quarkus тесты** (Kotlin) — тесты микросервиса визуализации
4. **End-to-end тесты** — полный стек Quarkus → Bridge → Bitrix24

---

## Уровень 1: Unit-тесты (Python)

### Запуск

```bash
python -m unittest discover -s tests -v
```

### Покрытие (62 теста)

| Файл | Класс | Тестов |
|------|-------|--------|
| `test_auth.py` | `TestWebhookAuth` | 8 |
| `test_auth.py` | `TestOAuth2Auth` | 8 |
| `test_client.py` | `TestFlattenParams` | 4 |
| `test_client.py` | `TestBitrix24ClientCall` | 6 |
| `test_client.py` | `TestGetAll` | 2 |
| `test_client.py` | `TestBatch` | 1 |
| `test_client.py` | `TestFromEnv` | 1 |
| `test_kanban.py` | `TestKanbanStage` | 2 |
| `test_kanban.py` | `TestKanbanCard` | 2 |
| `test_kanban.py` | `TestBoardState` | 2 |
| `test_kanban.py` | `TestKanbanBoard` | 7 |
| `test_smart_processes.py` | `TestPipelineStage` | 2 |
| `test_smart_processes.py` | `TestSmartProcessType` | 1 |
| `test_smart_processes.py` | `TestSmartItem` | 2 |
| `test_smart_processes.py` | `TestPipeline` | 4 |
| `test_smart_processes.py` | `TestSmartProcess` | 9 |

### Ключевые сценарии

#### WebhookAuth
- Инициализация через параметры и переменные окружения
- Формирование базового URL и endpoint-ов
- Ошибки при отсутствии обязательных параметров

#### OAuth2Auth
- Проверка истечения срока токена
- Логика обновления токена
- Параметры аутентификации

#### Bitrix24Client
- Успешные вызовы API
- Обработка ошибок API (APIError, NotFoundError)
- Автопагинация (get_all)
- Батч-запросы
- Преобразование вложенных параметров

#### KanbanBoard
- Получение и создание этапов (dict и list форматы)
- Создание и перемещение карточек
- Получение состояния доски
- Health-статус (healthy/error)

#### SmartProcess
- CRUD типов и элементов
- Переходы по этапам
- Управление workflow (start/pause/stop/delete)
- Health-статус

---

## Уровень 2: Интеграционные тесты (Python)

> Требуется реальный Bitrix24 портал с настроенным webhook.

### Подготовка

```bash
export BX24_DOMAIN="your-test-portal.bitrix24.com"
export BX24_USER_ID=1
export BX24_WEBHOOK_TOKEN="your_test_webhook_token"
```

### Ручное тестирование через CLI

```bash
# 1. Проверка подключения
python cli/main.py call user.current

# 2. Создание тестовых задач
python cli/main.py task add --title "Тест Kanban 1" --responsible 1
python cli/main.py task add --title "Тест Kanban 2" --responsible 1

# 3. Просмотр Kanban-доски
python cli/main.py task stages
python cli/main.py task list

# 4. Создание смарт-процесса
python cli/main.py smart type-list
# Если нет смарт-процессов, создайте через веб-интерфейс Bitrix24

# 5. Работа с элементами смарт-процесса
python cli/main.py smart list --type-id 128
python cli/main.py smart add --type-id 128 --title "Тестовый запрос"

# 6. Проверка бизнес-процессов
python cli/main.py bp templates
python cli/main.py bp list
```

### Тестовый сценарий (use-case: Service Desk)

```bash
# Service Desk Use Case
# Компания использует смарт-процесс "Service Requests"
# для управления заявками в службу поддержки

# 1. Создание заявок
python cli/main.py smart add --type-id 128 --title "Починить принтер в офисе 301"
python cli/main.py smart add --type-id 128 --title "Настроить ноутбук нового сотрудника"
python cli/main.py smart add --type-id 128 --title "Восстановить доступ к почте"

# 2. Просмотр всех заявок
python cli/main.py smart list --type-id 128

# 3. Переход заявки в работу (через API)
# python cli/main.py smart update --type-id 128 --id 1 --field "stageId=DT128_1:IN_PROGRESS"

# 4. Запуск бизнес-процесса уведомлений
# python cli/main.py bp start --template-id 5 --document crm:CCrmDynamicType_128:1

# 5. Завершение заявки
# python cli/main.py smart update --type-id 128 --id 1 --field "stageId=DT128_1:DONE"
```

---

## Уровень 3: Quarkus тесты

### Запуск

```bash
cd quarkus-stand
mvn test
```

### Что тестируется

- `VitrineResourceTest` — GET /vitrine/bundles возвращает 200 с mock-данными
  (при недоступном bridge используется fallback)

### Запуск с реальным bridge

```bash
# Терминал 1: запустить bridge
python bridge/server.py

# Терминал 2: запустить Quarkus тесты
cd quarkus-stand
mvn test -Dquarkus.test.profile=integration
```

---

## Уровень 4: End-to-end тесты

### Схема

```
[curl/Postman] --> [Quarkus :8080] --> [Python Bridge :5000] --> [Bitrix24 API]
```

### Запуск полного стека

```bash
# Терминал 1: Bridge
export BX24_DOMAIN=... BX24_WEBHOOK_TOKEN=...
python bridge/server.py

# Терминал 2: Quarkus Stand
cd quarkus-stand
mvn quarkus:dev
```

### Тест-кейсы

```bash
# Витрина
curl http://localhost:8080/vitrine/bundles

# Kanban-доска (entityType=1 = Мои задачи)
curl http://localhost:8080/kanban/1/board

# Смарт-процессы
curl http://localhost:8080/smart/types
curl http://localhost:8080/smart/128/state

# Бизнес-процессы
curl http://localhost:8080/bp/workflows

# Health check
curl http://localhost:8080/health
curl http://localhost:8080/health/ready

# Swagger UI
open http://localhost:8080/swagger-ui
```

---

## Чек-лист проверки

### Phase 1 (Core + CLI + Bundles)

- [ ] `python cli/main.py call user.current` — возвращает текущего пользователя
- [ ] `python cli/main.py task list` — возвращает список задач
- [ ] `python cli/main.py smart type-list` — список смарт-процессов
- [ ] `python -m unittest discover -s tests -v` — 62/62 тестов OK
- [ ] `python cli/main.py --format json call user.current` — JSON-вывод работает

### Phase 2 (Quarkus Stand)

- [ ] `bridge/server.py` запускается без ошибок
- [ ] `GET /api/v1/health` возвращает `{"status": "ok"}`
- [ ] `GET /api/v1/bundles/status` возвращает статусы бандлов
- [ ] Quarkus `mvn quarkus:dev` запускается
- [ ] `GET /vitrine/bundles` возвращает 200
- [ ] `GET /health/ready` возвращает UP или DOWN с понятным статусом

### Phase 3 (Testing)

- [ ] Все unit-тесты проходят
- [ ] Ручной тест CLI с реальным Bitrix24 работает
- [ ] End-to-end тест всего стека выполнен успешно

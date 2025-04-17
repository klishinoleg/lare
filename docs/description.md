# Корень

```
app/
├── domain/                # Чистый домен: сущности, интерфейсы, value-объекты, события
├── application/           # Бизнес-логика: use-case'ы, команды, обработка событий
├── infrastructure/        # Реализация интерфейсов: БД, API, адаптеры
├── interfaces/            # Внешний слой: HTTP, CLI, WebSocket и т.п.
├── core/                  # Конфиги, зависимости, DI, базовые утилиты
├── events/                # Центральная диспетчеризация и типы событий
├── tests/                 # Тесты
```

## 🧱 Архитектура проекта (DDD + Clean Architecture)

---

## 📁 `domain/`

**Описание:** Содержит фундаментальные строительные блоки бизнес-логики.

### Содержимое:

- `entities.py` — бизнес-сущности (`AccountEntity`)
- `interfaces.py` — абстрактные интерфейсы (`AccountRepository`)
- `value_objects.py` — объекты-значения (`Email`, `Credits`)
- `exceptions.py` — специфичные бизнес-исключения
- `events.py` — события уровня домена (`AccountCreated`)

---

## 📁 `application/`

**Описание:** Use-case'ы, команды, координация логики.

### Содержимое:

- `services.py` — бизнес-операции (`create_account`, `update_credits`)
- `commands.py` — входные DTO-команды (`CreateAccountCommand`)
- `handlers.py` — обработчики событий (`on_bill_paid`)
- `mappers.py` — преобразование entity ↔ DTO

---

## 📁 `infrastructure/`

**Описание:** Конкретные реализации интерфейсов из `domain`.

### Примеры:

- `db/account/models.py` — ORM-модель аккаунта
- `db/account/repository.py` — реализация `AccountRepository`
- `api/telegram/telegram_auth_provider.py` — Telegram-авторизация
- `adapters/auth/password_hasher.py` — хэшер пароля
- `messaging/telegram_bot.py` — отправка сообщений

---

## 📁 `interfaces/`

**Описание:** Входной слой: HTTP, CLI и т.п.

### Примеры:

- `http/routes/account.py` — FastAPI эндпоинты
- `http/schemas/account.py` — Pydantic DTO
- `cli/entrypoint.py` — команды через терминал

---

## 📁 `core/`

**Описание:** Общие зависимости и конфигурации.

### Примеры:

- `config.py` — настройки из `.env` через `pydantic.BaseSettings`
- `di.py` — фабрики и DI-контейнеры (`get_repository`)
- `utils.py` — базовые вспомогательные функции

---

## 📁 `events/`

**Описание:** Реализация событийной системы.

### Примеры:

- `bus.py` — реализация EventBus или MessageDispatcher
- `types.py` — перечисление событий
- `handlers/` — логика, реагирующая на события

---

## 📁 `tests/`

**Описание:** Покрытие логики на всех уровнях.

### Структура:

- `domain/` — тесты бизнес-сущностей
- `application/` — тесты use-case'ов
- `infrastructure/` — тесты реализаций
- `interfaces/` — тесты API-слоя
- `fixtures/` — мок-данные и подготовка

---

## 📌 Ключевые принципы

- **domain** — центр проекта, чистый от фреймворков
- **application** — управляет потоком и логикой
- **infrastructure** — реализует доступ к данным, API и т.п.
- **interfaces** — то, как внешний мир общается с системой
- **всё заменяемо и тестируемо**

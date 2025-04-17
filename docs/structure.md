```
app/
├── domain/                  # Чистый домен: сущности, интерфейсы, value-объекты, события
│   └── account/
│       ├── entities.py         # AccountEntity (id, credits, username и т.д.)
│       ├── interfaces.py       # AccountRepository, AccountSettingsProvider
│       ├── value_objects.py    # Email, Credits, LanguageCode и т.п.
│       ├── exceptions.py       # Специфичные ошибки
│       └── events.py           # Domain-события (AccountCreated, CreditsChanged)

├── application/             # Use-case'ы, команды, логика, обработка событий
│   └── account/
│       ├── services.py         # AccountService или UseCase (create, update_credits)
│       ├── commands.py         # DTO-команды: CreateAccountCommand
│       ├── handlers.py         # Обработчики событий
│       └── mappers.py          # Entity <-> DTO преобразования

├── infrastructure/          # Реализация интерфейсов из domain
│   ├── db/
│   │   └── account/
│   │       ├── models.py       # Tortoise/SQLAlchemy модели
│   │       └── repository.py   # TortoiseAccountRepository
│   ├── api/
│   │   └── telegram/
│   │       └── telegram_auth_provider.py
│   ├── messaging/
│   │   └── telegram_bot.py
│   └── adapters/
│       └── auth/
│           └── password_hasher.py

├── interfaces/              # Входной слой: HTTP, CLI и т.п.
│   ├── http/
│   │   ├── routes/
│   │   │   ├── auth.py         # FastAPI endpoints
│   │   │   └── account.py
│   │   └── schemas/
│   │       ├── auth.py         # Pydantic DTO: LoginRequest, AuthResponse
│   │       └── account.py
│   └── cli/
│       └── entrypoint.py

├── core/                    # Конфигурация и DI
│   ├── config.py             # Настройки из .env
│   ├── di.py                 # Dependency Injection / get_repository()
│   └── utils.py

├── events/                  # События и EventBus
│   ├── bus.py                # EventDispatcher
│   ├── types.py              # EventNameEnum
│   └── handlers/
│       └── billing.py

├── tests/                   # Тесты
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   ├── interfaces/
│   └── fixtures/
```

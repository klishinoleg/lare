# LazyReader Backend (Clean Architecture)

## Project Overview

LazyReader is a backend system designed using the principles of **Clean Architecture**.
Its primary goal is to separate concerns between domain logic, application services, infrastructure layers, and interfaces to ensure long-term maintainability, scalability, and testability.

LazyReader focuses on **text analysis in foreign languages** and **learning words and phrases**.
Users can parse articles, subtitles, or book chapters, translate sentences, analyze word structures, and save vocabulary for repetition.

The system strictly follows Domain-Driven Design (DDD) practices with clear module separation and strong typing throughout the project.

**Current public version:**

- [Website (description)](https://lazy-reader.com/)
- [Telegram App (application)](https://t.me/lazyreader_bot)

## Project Goals

- **Clean Architecture** separation:
  - **Domain Layer**: Core business entities, value objects, domain events, and repositories as pure Python code.
  - **Application Layer**: Use cases, commands, and service orchestration.
  - **Infrastructure Layer**: Concrete implementations like database repositories, external API integrations, mock services.
  - **Interface Layer**: HTTP (FastAPI), CLI, and WebSocket endpoints.
  - **Core Layer**: Configuration, utilities, enums, and dependency injection.
- **Strict Interfaces and Abstractions**:
  - No domain object directly depends on frameworks, ORMs, or APIs.
- **Dynamic Repository Resolution**:
  - Repository implementations are dynamically loaded based on entity and storage type.
- **Flexible Persistence Layer**:
  - Switch between Tortoise ORM (PostgreSQL/SQLite), Redis, or Mock repositories without changing business logic.
- **Advanced Access Control**:
  - Role and ownership-based access validation integrated into service methods.
- **Robust Exception Handling**:
  - Centralized domain exceptions and validation errors.

## Architecture Summary

```
app/
├── domain/                # Pure domain logic: entities, interfaces, exceptions
├── application/           # Use cases, services, validation
├── infrastructure/        # Repository implementations (Tortoise ORM, Mock, etc.)
├── interfaces/            # API endpoints (FastAPI), CLI commands
├── core/                  # Configuration, enums, helpers, DI
├── events/                # Event system and event handlers
tests/                     # Test coverage across layers
```

## Tech Stack

- **Python 3.12+**
- **FastAPI** for web layer
- **Tortoise ORM** for async database operations
- **Pydantic** for validation and settings
- **PostgreSQL/SQLite** as databases
- **Redis** (planned) for future caching layers
- **Kafka/FastStream** (future) for event-driven modules

## Status

The core architecture is fully established, and development of specific modules (Books, Chapters, Subtitles, Word Parsing) is ongoing.

## License

This project is under a proprietary license.
All rights reserved © LazyReader team.

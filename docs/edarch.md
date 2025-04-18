# 📚 Event-Driven Architecture for LazyReader Project

## 1. Project Structure:

```
app/
├── core/
│   └── config.py                # Configuration + Kafka broker settings
│   └── di/                      # Dependency injection for repositories, services, and events
│
├── domain/
│   ├── book/
│   │   ├── entities.py
│   │   └── exceptions.py
│   │   └── interfaces/
│   │        └── repository.py
│   ├── chapter_word/
│   │   └── entities.py
│
├── application/
│   ├── book/
│   │   ├── services/
│   │   │    └── create_chapter_service.py  # UseCase for chapter creation
│   │   ├── events/
│   │   │    └── saga_create_chapter.py     # Saga to manage the lifecycle of chapter creation
│   └── events/
│       └── publisher.py                    # Kafka event publishers
│       └── subscriber.py                   # Kafka event subscribers
│
├── events/
│   ├── driver.py                # EventDriverManager
│   ├── event_bus.py             # FastStream Kafka client wrapper
│   ├── event_types.py           # Event type constants
│   ├── base.py                  # Base Event class
│
├── infrastructure/
│   └── repository/
│       └── tortoise/
│           └── models/
│
└── interfaces/
    └── fastapi/
        ├── routers/
        │   └── book.py          # HTTP endpoint to create a chapter
```

---

## 2. Saga: Chapter Creation (Group 1)

| Step | Event                        | Action                     | Description                                                   |
| :--- | :--------------------------- | :------------------------- | :------------------------------------------------------------ |
| 1    | `chapter.create.requested`   | Chapter creation requested | Save basic chapter record in DB or publish full text to Kafka |
| 2    | `chapter.text.processed`     | Text processed             | Process text into words using `split_text_into_words.py`      |
| 3    | `chapter.words.saved`        | Words saved                | Save words to database (`WordChapter` indexes)                |
| 4    | `chapter.creation.completed` | Chapter creation completed | Final step, notifying completion                              |
| 5    | `chapter.creation.error`     | Error occurred             | If any error happens, publish an error event                  |

---

## 3. Technology Stack:

| Component   | Usage                                          |
| :---------- | :--------------------------------------------- |
| Kafka       | Event broker                                   |
| FastStream  | Kafka client for async producer/consumer       |
| JSON Schema | Serialization and validation of event payloads |
| DTOs        | Structured event payloads                      |

---

## 4. Technical Workflow:

1. User sends a chapter creation request via FastAPI → A basic chapter record is saved and `chapter.create.requested` event is published.
2. Kafka consumer catches `chapter.create.requested` → Text is processed → `chapter.text.processed` event is published.
3. Kafka consumer catches `chapter.text.processed` → Words are saved to the database → `chapter.words.saved` event is published.
4. Kafka consumer catches `chapter.words.saved` → Chapter creation is finalized → `chapter.creation.completed` is published.
5. If an error occurs during any step → `chapter.creation.error` is published.

---

# 🛠 Next Steps:

1. Create:

   - `events/event_types.py`
   - `events/base.py`
   - `events/driver.py`
   - `events/event_bus.py`

2. Define event DTOs:

   - `CreateChapterRequestedEvent`
   - `ChapterTextProcessedEvent`
   - `ChapterWordsSavedEvent`
   - `ChapterCreationCompletedEvent`
   - `ChapterCreationErrorEvent`

3. Setup FastStream minimal producer/consumer (`event_bus.py`).

4. Create the basic saga `saga_create_chapter.py` to handle the event chain.

---

## ✏️ Quick Recap:

| Item                                        | Status |
| :------------------------------------------ | :----- |
| Kafka as broker                             | ✅     |
| FastStream client library                   | ✅     |
| Chapter creation event group                | ✅     |
| Saga-based event management                 | ✅     |
| Future groups (translations, audio) planned | ✅     |

---

## Final question:

**Shall we proceed with creating folders + the base `EventDriverManager` + basic event constants (`event_types.py`)?**

If yes — I will immediately structure it properly for your LazyReader project. 🚀

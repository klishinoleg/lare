# Book & Chapter

## Flow

```
FastAPI DTO → BookService / ChapterService → validate authorship / input
→ call domain: Book.add_chapter(), Chapter.set_content() → update repositories
→ return Book or ChapterDTO with metadata
```

## Structure

```
domain/
└── book/
    ├── book.py                        # Book entity (aggregate root)
    ├── chapter.py                     # Chapter entity
    ├── exceptions.py                  # BookNotFound, ChapterNotFound, NotAuthor
    ├── dtos.py                        # ChapterInputDTO, ChapterTypeDTO
    ├── interfaces/
    │   └── repository.py              # BookRepository, ChapterRepository
    └── services/
        ├── book_service.py           # Book logic: add, sort, check authorship
        └── chapter_service.py        # Chapter logic: content processing
```

## Relation with Application Layer

```
application/
└── book/
    ├── dtos.py                        # CreateBookDTO, CreateChapterDTO, SortChaptersDTO
    ├── commands.py                    # AddChapterCommand, SortChaptersCommand
    └── services/
        ├── book_command_service.py   # wraps domain BookService with transaction
        └── chapter_command_service.py# wraps Chapter logic for controller use

```

# Word

## Flow

```
ChapterService → split → WordService.get_or_create()
→ WordRepository → return Word
→ ChapterWordIndexService.create(indexed word with position, symbol form)

```

##Structure

```
domain/
└── word/
    ├── word.py                        # Word aggregate with AI logic
    ├── exceptions.py                  # WordNotFound, AIWordError
    ├── dtos.py                        # WordInfoDTO, EtymologyDTO
    ├── interfaces/
    │   └── repository.py              # WordRepository
    └── services/
        ├── word_service.py           # Get/create word, generate etymology
        └── voice_service.py          # Generate AI voice
```

##Relation with Application Layer

```
application/
└── word/
    ├── dtos.py                        # WordWithTranslationDTO
    ├── commands.py                    # GenerateWordVoiceCommand
    └── services/
        └── word_command_service.py   # Used by chapter or fastapi layer
```

#IndexChapterWord
##Flow

```
ChapterService.set_content() → for word in text: → WordService.get_or_create()
→ ChapterWordIndexService.index(word, chapter, position, symbols, phrase)
```

##Structure

```
domain/
└── chapter_word_index/
    ├── index_chapter_word.py         # IndexChapterWord entity
    ├── dtos.py                        # WordPositionDTO, WordSymbolDTO
    ├── interfaces/
    │   └── repository.py              # ChapterWordIndexRepository
    └── services/
        └── index_service.py          # Logic to build/rebuild indexes
```

##Relation with Application Layer

```
application/
└── chapter_word_index/
    ├── dtos.py                        # IndexWordsCommandDTO
    └── services/
        └── index_command_service.py  # Service used by ChapterCommandService
```

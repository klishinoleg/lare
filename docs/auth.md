# Auth

## Flow

```
Telegram DTO → TelegramProvider → validate → extract → AuthorizationProfileData
→ AuthService → check_or_create_profile → get_or_create_account → return token + user
```

## Structure

```
domain/
└── authorization_profile/
    ├── entities.py                     # AuthorizationProfileEntity
    ├── exceptions.py                   # InvalidAuthProfileError
    ├── enums.py                        # AuthProviderType
    ├── interfaces/
    │   ├── repository.py               # AuthorizationProfileRepository
    │   ├── provider.py                 # BaseAuthProvider (abstract)
    ├── services/
    │   ├── authorize.py                # AuthProfileService (core logic)
    └── factories/
        └── provider_factory.py         # resolve_provider()
```

## Relation with Application Layer

```
application/
└── authorization/
    ├── dtos.py                         # TelegramInitDTO
    ├── services/
    │   └── auth_via_profile.py         # main app service

```
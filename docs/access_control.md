###domain/access_control

```
domain/
└── access_control/
    ├── interfaces/
    │   └── validator.py              # BaseValidator with has_access()
    ├── services/
    │   └── authorizer.py             # Authorizer: register(), can_edit(), or_raise()
    ├── exceptions.py                 # PermissionDenied, BookPermissionDenied и др.

```

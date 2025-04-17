from enum import IntEnum


class AccessRole(IntEnum):
    SUPERUSER = 1
    ADMINISTRATOR = 5
    NOT_ROLE = 500

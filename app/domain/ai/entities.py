from dataclasses import dataclass
from decimal import Decimal
from domain.abstract import BaseEntity
from domain.finance.enums.account_usage_type import AccountUsageType
from domain.mixins.timestamp_mixin import TimestampMixin
from domain.mixins.with_active_mixin import WithActiveMixin


@dataclass(slots=True, kw_only=True)
class AiLogEntity(BaseEntity, TimestampMixin):
    """
    Stores a single request and response pair sent to an external AI provider.

    This entity is used solely for logging purposes and tracks:
    - what was sent to the AI (prompt),
    - what was received (response),
    - who initiated the request (account),
    - which model and type was used,
    - what the usage type was (e.g., translation, TTS),
    - the hash to enable de-duplication or caching logic.

    Attributes:
        ai_request (str): The input prompt or original text sent to the provider.
        ai_response (str): The response or translated/generated text from the provider.
        ai_type (str): The type of provider used (e.g., "chatgpt", "google_translate").
        ai_model_id (int): Foreign key reference to the AiModelEntity used.
        file_path (str): The path to the file that was reciev from provider (voice, image).
        source_language (int): Foreign key reference to the source language.
        target_language (int): Foreign key reference to the target language.
        usage_type (AccountUsageType): Purpose of the request (translation, voice, etc.).
        account_id (int): ID of the user account that made the request.
        hash_str (str): SHA256 hash of the request to detect duplicate calls.
    """
    ai_request: str
    ai_response: str
    ai_type: str
    ai_model_id: int
    file_path: str | None
    source_language: int
    target_language: int | None
    usage_type: AccountUsageType
    account_id: int
    hash_str: str


@dataclass(slots=True, kw_only=True)
class AiModelEntity(BaseEntity, WithActiveMixin):
    """
    Describes a registered AI model, including its pricing and allowed usages.

    This entity defines which AI models are available in the system and
    supports dynamic cost calculation per provider.

    Attributes:
        name (str): Display name of the model, e.g. "GPT-4 Chat".
        model (str): Internal or provider-specific ID (used in API requests).
        input_cost (Decimal): Cost per 1k input tokens/chars in base currency.
        output_cost (Decimal | None): Cost per 1k output tokens, if applicable.
        kef (int): Multiplier applied to pricing (for markup, discounts).
        allow_to (list[AccountUsageType]): List of allowed usage types (e.g., only TTS).
    """
    name: str
    model: str
    input_cost: Decimal
    output_cost: Decimal | None = None
    kef: int = 1
    allow_to: list[AccountUsageType]

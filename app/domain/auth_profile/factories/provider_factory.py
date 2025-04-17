from typing import Type

from core.messages.exceptions import GetExMessages
from domain.auth_profile.enums import AuthProviderType
from domain.auth_profile.interfaces.provider import BaseAuthProvider
from domain.auth_profile.exceptions import AuthProviderNotRegistered


class AuthProviderFactory:
    """
    Factory class for resolving authentication provider implementations
    based on the given AuthProviderType enum.

    Usage:
        provider = AuthProviderFactory.get_provider(AuthProviderType.TELEGRAM)
        entity = provider.validate_and_parse(provider_data)

    This approach allows dynamic selection of a provider based on incoming data.
    """

    _providers: dict[AuthProviderType, Type[BaseAuthProvider]] = {}

    @classmethod
    def register(cls, provider_cls: Type[BaseAuthProvider]):
        """
        Register a new provider class with the factory.

        The provider must implement `BaseAuthProvider` and define `provider_type()`.

        Args:
            provider_cls (Type[BaseAuthProvider]): The class to register.
        """
        cls._providers[provider_cls.provider_type()] = provider_cls

    @classmethod
    def get_provider(cls, provider_type: AuthProviderType) -> BaseAuthProvider:
        """
        Retrieve a provider instance by provider type.

        Args:
            provider_type (AuthProviderType): The enum identifying the provider.

        Returns:
            BaseAuthProvider: The corresponding provider instance.

        Raises:
            AuthProfileInvalidCredentialsError: If provider is not registered.
        """
        provider_cls = cls._providers.get(provider_type)
        if not provider_cls:
            raise AuthProviderNotRegistered(GetExMessages.auth_provider_not_registered(provider_type),
                                            field="provider_type")
        return provider_cls()

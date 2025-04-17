from __future__ import annotations
from pydantic import BaseModel, Field
from application.auth.dtos import AuthInitDataDTO
from domain.auth_profile.enums import AuthProviderType


class BasePasswordAuthProviderDTO(BaseModel):
    ...


class PasswordRegistrationDTO(BasePasswordAuthProviderDTO):
    password: str = Field(..., description='Password')
    repeat_password: str = Field(..., description='Repeat password')
    username: str = Field(..., description='Username')
    language_code: str = Field(..., description='Language code')
    public_name: str | None = Field(None, description='Public name')


class PasswordLoginDTO(BasePasswordAuthProviderDTO):
    username: str = Field(..., description='Username')
    password: str = Field(..., description='Password')


class ChangePasswordDTO(BasePasswordAuthProviderDTO):
    password: str = Field(..., description='Password')
    repeat_password: str = Field(..., description='Repeat password')


class BasePasswordInitDTO(AuthInitDataDTO):
    provider_type: AuthProviderType = Field(default=AuthProviderType.PASSWORD, description='Password provider type')


class PasswordRegistrationInitDataDTO(BasePasswordInitDTO):
    provider_data: PasswordRegistrationDTO = Field(..., description="Password registration data DTO")


class PasswordLoginInitDataDTO(BasePasswordInitDTO):
    provider_data: PasswordLoginDTO = Field(..., description="Password login data DTO")


class ChangePasswordInitDataDTO(BasePasswordInitDTO):
    provider_data: ChangePasswordDTO = Field(..., description="Password registration data DTO")

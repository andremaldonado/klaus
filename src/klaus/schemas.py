from pydantic import BaseModel, Field, field_validator
from typing import List


class ChatRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000,
                      description="Mensagem do usuário para o Klaus")


class AuthCodeRequest(BaseModel):
    code: str = Field(..., min_length=10, description="Authorization code do Google")


class ListCommand(BaseModel):
    list_name: str
    items: List[str]

    @field_validator("items")
    def clean_items(cls, v):
        return [item.strip().lower() for item in v if item.strip()]

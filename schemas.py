# schemas.py
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000,
                      description="Mensagem do usuário para o Klaus")

class AuthCodeRequest(BaseModel):
    code: str = Field(..., min_length=10, description="Authorization code do Google")

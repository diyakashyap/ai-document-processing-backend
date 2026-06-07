from pydantic import BaseModel, EmailStr


class EmailLoginRequest(BaseModel):
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: EmailStr
    expires_in: int

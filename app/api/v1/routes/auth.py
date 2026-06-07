from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.schemas.auth import EmailLoginRequest, TokenResponse
from app.services.user_service import get_or_create_user

router = APIRouter()


@router.post("/token", response_model=TokenResponse)
def generate_token(payload: EmailLoginRequest, db: Session = Depends(get_db)):
    user = get_or_create_user(db, payload.email)
    return TokenResponse(
        access_token=create_access_token(user.email),
        email=user.email,
        expires_in=settings.access_token_expire_minutes * 60,
    )

from sqlalchemy.orm import Session

from app.models.user import User


def get_or_create_user(db: Session, email: str) -> User:
    normalized_email = email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()
    if user:
        return user

    user = User(email=normalized_email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.document import Document, ProcessingStatus
from app.models.user import User
from app.schemas.document import UserStatsResponse

router = APIRouter()


@router.get("", response_model=UserStatsResponse)
def get_user_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Document).filter(Document.user_id == current_user.id)
    documents = query.all()
    return UserStatsResponse(
        total_files=len(documents),
        completed=sum(doc.status == ProcessingStatus.completed for doc in documents),
        processing=sum(doc.status == ProcessingStatus.processing for doc in documents),
        failed=sum(doc.status == ProcessingStatus.failed for doc in documents),
    )

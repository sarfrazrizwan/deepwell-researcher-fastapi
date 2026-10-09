from datetime import datetime

from sqlalchemy import DateTime, String, ForeignKey
from uuid import UUID, uuid4
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.enums import ThreadStatus

from app.db.base import Base, TimestampMixin


class Thread(TimestampMixin, Base):
    __tablename__ = "threads"
    
    id: Mapped[UUID] = mapped_column(
            PG_UUID(as_uuid=True),
            primary_key=True,
            default=uuid4
        )
    
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255), nullable=True, default=None)
    status: Mapped[ThreadStatus] = mapped_column(default=None, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(), default=None, nullable=True)
    
    user: Mapped["User"] = relationship(back_populates="threads")
